
#!/usr/bin/env python3
"""
This file holds HX711 class and LoadCell class which is used within HX711 in order to track multiple load cells
"""

from time import sleep, perf_counter
from statistics import mean, median, stdev
from random import randint
from hx711.utils import convert_to_list

SIMULATE_PI = False
try:
    import RPi.GPIO as GPIO
except: 
    # set to simulate mode if unable to import GPIO (non raspberry pi run)
    SIMULATE_PI = True

class HX711:
    """
    HX711 class holds data for one or multiple load cells. All load cells must be using the same clock signal and be the same channel and gain setting
    
    Args:
        dout_pin (int or [int]): Raspberry Pi GPIO pins where data from HX711 is received
        sck_pin (int): Raspberry Pi clock output pin where sck signal to HX711 is sent
        gain_channel_A (int): Optional, by default value 128. Options (128 || 64)
        select_channel (str): Optional, by default 'A'. Options ('A' || 'B')
        debug_mode (bool): Optional, False by default

    Raises:
        TypeError:
            if dout_pins not an int or list of ints
            if gain_channel_A or select_channel not match required values
    """
    
    def __init__(self,
                 dout_pins,
                 sck_pin: int,
                 channel_A_gain: int = 128,
                 channel_select: str = 'A',
                 debug_mode: bool = False,
                 ):
        
        self._debug_mode = debug_mode
        self._set_dout_pins(dout_pins)
        self._set_sck_pin(sck_pin)
        # init GPIO before channel because a read operation is required for channel initialization
        self._init_gpio()
        self._set_channel_a_gain(channel_A_gain)
        self._set_channel_select(channel_select)
        self._init_load_cells()
                
    def _set_dout_pins(self, dout_pins):
        # set dout_pins as array of ints. If just an int input, turn it into a single array of int
        self._dout_pins = convert_to_list(dout_pins, _type=int, _default_output=None)
        if self._dout_pins is None:
            # raise error if pins not set properly
            raise TypeError(f'dout_pins must be type int or array of int.\nReceived dout_pins: {dout_pins}')
        
    def _set_sck_pin(self, sck_pin):
        # set sck_pin if int
        if type(sck_pin) is not int:
            raise TypeError(f'sck_pin must be type int.\nReceived sck_pin: {sck_pin}')
        self._sck_pin = sck_pin
                    
    def _init_gpio(self):
        # init GPIO
        if not SIMULATE_PI:
            GPIO.setup(self._sck_pin, GPIO.OUT)  # sck_pin is output only
            for dout in self._dout_pins:
                GPIO.setup(dout, GPIO.IN)  # dout_pin is input only
            
    def _set_channel_a_gain(self, channel_A_gain):
        # check channel_select for type and value. Default is A if None
        if channel_A_gain not in [128, 64]:
            # raise error if channel not 128 or 64
            raise TypeError(f'channel_A_gain must be A or B.\nReceived channel_A_gain: {channel_A_gain}')
        self._channel_A_gain = channel_A_gain
        
    def _set_channel_select(self, channel_select):
        # check channel_select for type and value. Default is A if None
        if channel_select not in ['A', 'B']:
            # raise error if channel not A or B
            raise TypeError(f'channel_select must be A or B.\nReceived channel_select: {channel_select}')
        self._channel_select = channel_select
                
    def _init_load_cells(self):
        # initialize load cell instances
        self._load_cells = []
        for dout_pin in self._dout_pins:
            self._load_cells.append(LoadCell(dout_pin, self._debug_mode))

    def _prepare_to_read(self):
        """
        prepare to read by setting SCK output to LOW and loop until all dout inputs are LOW

        Returns:
            bool : True if ready to read else False 
        """
        if SIMULATE_PI:
            return True
        
        GPIO.output(self._sck_pin, False)  # start by setting the pd_sck to 0
        
        # check if ready a maximum of 20 times (~200ms)
        ready = True
        for _ in range(20):
            # confirm all dout pins are ready (LOW)
            ready = True
            load_cell: LoadCell
            for load_cell in self._load_cells:
                if GPIO.input(load_cell._dout_pin) == 0:
                    ready = False
            if ready:
                break
            else:
                # if not ready sleep for 10ms before next iteration
                sleep(0.01)                
        return ready
    
    def _pulse_sck_high(self):
        """
        Pulse SCK pin high shortly
        
        Returns:
            bool: True if pulse was shorter than 60 ms
        """
        
        if SIMULATE_PI:
            return True
        
        pulse_start = perf_counter()
        GPIO.output(self._sck_pin, True)
        GPIO.output(self._sck_pin, False)
        pulse_end = perf_counter()
        # check if pulse lasted 60ms or longer. If so, HX711 enters power down mode
        if pulse_end - pulse_start >= 0.00006:  # check if the hx 711 did not turn off...
            # if pd_sck pin is HIGH for 60 us and more than the HX 711 enters power down mode.
            if self._debug_mode:
                print(f'sck pulse lasted for longer than 60ms\nTime elapsed: {pulse_end - pulse_start}')
            return False
        return True
    
    def _write_channel_gain(self):
        """
        _write_channel_gain must be run after each 24-bit read
        pulses SCK pin 1, 2, or 3 times based on channel configuration
        
        A, 128 : total pulses = 25 (24 read data, 1 extra to set dout back to high)
        A, 64 : total pulses = 27 (24 read data, 3 extra to set dout back to high)
        B, 32 : total pulses = 26 (24 read data, 2 extra to set dout back to high)
        
        Returns:
            bool: True if pulsees were all successful
        """
        
        # get number of pulses based on channel configuration
        num_pulses = 2 # default 2 for channel B
        if self._channel_select == 'A' and self._channel_A_gain == 128:
            num_pulses = 1
        elif self._channel_select == 'A' and self._channel_A_gain == 64:
            num_pulses = 3
        
        # pulse num_pulses
        for _ in range(num_pulses):
            if not self._pulse_sck_high():
                return False
        return True
            
        
        
    def _read(self):
        """
        _read performs a single datapoint read across all load cells. The data is stored within the LoadCell instances
        read each bit from HX711, convert to signed int, and validate
        operation:
            1) set SCK output HIGH, loop until all dout pins are LOW (_prepare_to_read)
            2) read first 24 bits of each LoadCell by pulsing SCK output for each bit
            3) set channel gain following read by pulsing SCK to result in a total of 25, 26, or 27 SCK pulses for a read operation (see documentation)
        
        Returns:
            bool : returns True if successful. Readings are assigned to LoadCell objects
        """
        
        # prepare for read by setting SCK pin and checking that each load cell is ready
        if not self._prepare_to_read():
            if self._debug_mode:
                print('_prepare_to_read() not ready after 20 iterations\n')
            return False
        
        # read first 24 bits of data (the raw data bits)
        load_cell: LoadCell
        # init each load cell raw read data
        for load_cell in self._load_cells:
            load_cell._init_raw_read()
        # for each bit in 24 bits, perform load cell read
        for _ in range(24):
            # pulse sck high to request each bit
            if not self._pulse_sck_high():
                return False
            for load_cell in self._load_cells:
                load_cell._read()
        # finalize each load cell raw read
        for load_cell in self._load_cells:
            load_cell._finish_raw_read()
                
        # set channel after read
        if not self._write_channel_gain():
            return False
        
        return True
    
    def read_raw(self, readings_to_average: int = 10):
        """ read raw data for all load cells, does not perform unit conversion

        Args:
            readings_to_average (int, optional): number of raw readings to average together. Defaults to 10.

        Returns:
            list of int: returns raw data measurements without unit conversion
        """
        
        if not (1 <= readings_to_average <= 100):
            raise ValueError(f'Parameter "readings_to_average" must be between 1 and 99. Received: {readings_to_average}')
        
        load_cell: LoadCell
        # init each load cell for a set of reads
        for load_cell in self._load_cells:
            load_cell._init_set_of_reads()
        # perform reads
        for _ in range(readings_to_average):
            self._read()
        # for each load cell, calculate measurement values
        for load_cell in self._load_cells:
            load_cell._calculate_measurement()
            
        if self._debug_mode:
            print(f'Finished read operation. Load cell results:\n{"\n".join([str(vars(load_cell)) for load_cell in self._load_cells])}')

        load_cell_measurements = [load_cell.measurement_from_offset for load_cell in self._load_cells]
        return load_cell_measurements
    
    def read_weight(self, readings_to_average: int = 10):
        """ read raw data for all load cells and then return with weight conversion

        Args:
            readings_to_average (int, optional): number of raw readings to average together. Defaults to 10.

        Returns:
            list of int: returns data measurements with weight conversion
        """
        
        # perform raw read operation to get means and then offset and divide by weight multiple
        self.read_raw(readings_to_average)
        load_cell_weights = [load_cell.weight for load_cell in self._load_cells]
        return load_cell_weights
    
    def power_down(self):
        """ turn off the hx711 by setting SCK pin LOW then HIGH """
        
        if not SIMULATE_PI:
            GPIO.output(self._sck_pin, False)
            GPIO.output(self._sck_pin, True)
        sleep(0.01)
        
    def power_up(self):
        """ turn on the hx711 by setting SCK pin LOW """
        
        if not SIMULATE_PI:
            GPIO.output(self._sck_pin, False)
        sleep(0.01)
        
    def reset(self):
        """ resets the hx711 and prepare it for the next reading.

        Returns: True if pass, False if readings do not come back
        """
        self.power_down()
        self.power_up()
        result = self.read_raw(6)
        if result:
            return True
        else:
            return False
        
    def zero(self, readings_to_average: int = 30):
        
        self.read_raw(readings_to_average)
        load_cell: LoadCell
        for load_cell in self._load_cells:
            load_cell.zero_from_mean()
            
class LoadCell:
    """
    LoadCell class holds data for one load cell
    """
    
    def __init__(self,
                 dout_pin,
                 debug_mode,
                 ):
        self._dout_pin = dout_pin
        self._debug_mode = debug_mode
        self._offset = 0.
        self._weight_multiple = 1.
        self._last_raw_read = None
        self.raw_reads = []
        self.reads = []
        self._reads_filtered = []
        self._max_stdev_from_med = 1.0 # maximium deviation from median
        self._read_med = None
        self._devs_from_med = []
        self._read_stdev = 0.
        self._ratios_to_stdev = []
        self.measurement = None # mean of reads
        self.measurement_from_offset = None # measurement minus offset
        self.weight = None # measurement_from_offset divided by weight_multiple
        
    def zero_from_mean(self):
        """ sets offset based on current value for measurement """
        if self.measurement:
            self._offset = self.measurement
        else:
            raise ValueError(f'Trying to zero LoadCell (dout={self._dout_pin}) with a bad mean value\nValue of measurement: {self.measurement}')
        
    def set_weight_multiple(self, weight_multiple: float):
        """ simply sets multiple. example: scale indicates value of 5000 for 1 gram on scale, weight_multiple = 5000 """
        self._weight_multiple = weight_multiple
        
    def _init_set_of_reads(self):
        """ init arrays and calculated values before beginning a set of reads for a measurement """
        self.raw_reads = []
        self.reads = []
        self._reads_filtered = []
        self._read_med = None
        self._devs_from_med = []
        self._read_stdev = 0.
        self._ratios_to_stdev = []
        self.measurement = None
    
    def _init_raw_read(self):
        """ set raw read value to zero, so each bit can be shifted into this value """
        self._current_raw_read = 0
    
    def _read(self):
        """ left shift by one bit then bitwise OR with the new bit """
        
        if not SIMULATE_PI:
            self._current_raw_read = (self._current_raw_read << 1) | GPIO.input(self._dout_pin)
        else:
            # if simulate, generate random 0 or 1 for data
            self._current_raw_read = (self._current_raw_read << 1) | randint(0,1)
        
    def _finish_raw_read(self):
        """ append current raw read value and signed value to raw_reads list and reads list """
        self.raw_reads.append(self._current_raw_read)
        # convert to signed value
        self._current_signed_value = self.convert_to_signed_value(self._current_raw_read)
        self.reads.append(self._current_signed_value)
        if self._debug_mode:
            # print 2's complement value and signed value
            print(f'Binary value as received: {bin(self._current_raw_read)}\nSigned value: {self._current_signed_value}')
            
    def convert_to_signed_value(self, raw_value):
        # convert to signed value after verifying value is valid
        #check if data is valid by checking betwwen valid range: 0x800000 - 0x7fffff
        if not (0x7fffff < raw_value < 0x800000):
            if self._debug_mode:
                print('Invalid raw value detected: {}\n'.format(raw_value))
            return None  # return None because the data is invalid
        # calculate int from 2's complement
        # check if the sign bit is 1, indicating a negative number
        if (raw_value & 0x800000):
            signed_value = -((raw_value ^ 0xffffff) + 1)  # convert from 2's complement to negative int
        else:  # else do not do anything the value is positive number
            signed_value = raw_value
        return signed_value
        
    def _calculate_measurement(self):
        """
        analyzes read values to calculate mean value
            1) filter by valid data only
            2) calculate median and standard deviations from median
            3) filter based on the standard deviations from the median
            4) calculate mean of remaining values

        Returns:
            bool: pass or fail boolean based on filtering of data
        """
        
        # filter reads to valid data only
        self._reads_filtered = [r for r in self.reads if ((r is not None) and (type(r) is int))]
        if not self._reads_filtered:
            # no values after filter, so return False to indicate no read value
            return False
        
        # get median and deviations from med
        self._read_med = median(self._reads_filtered)
        self._devs_from_med = [(abs(r - self._read_med)) for r in self._reads_filtered]
        self._read_stdev = stdev(self._devs_from_med)
        
        # filter by number of standard deviations from med
        if self._read_stdev:
            self._ratios_to_stdev = [(dev / self._read_stdev) for dev in self._devs_from_med]
        else:
            # stdev is 0. Therefore set to the median
            self.measurement = self._read_med
            return True
        _new_reads_filtered = []
        for (read_val, ratio) in zip(self._reads_filtered, self._ratios_to_stdev):
            if ratio <= self._max_stdev_from_med:
                _new_reads_filtered.append(read_val)
        self._reads_filtered = _new_reads_filtered
        
        # get mean value
        if not self._reads_filtered:
            # no values after filter, so return False to indicate no read value
            return False
        self.measurement = mean(self._reads_filtered)
        self.measurement_from_offset = self.measurement - self._offset
        self.weight = self.measurement_from_offset / self._weight_multiple
        
        return True