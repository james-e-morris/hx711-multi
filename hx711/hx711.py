
#!/usr/bin/env python3
"""
This file holds HX711 class and LoadCell class which is used within HX711 in order to track multiple load cells
"""

from hx711.utils import convert_to_list

SIMULATE_PI = False
try:
    import RPi.GPIO as GPIO
except: 
    # set to simulate mode if unable to import GPIO (non raspberry pi run)
    SIMULATE_PI = True

class HX711:
    """
    HX711 class holds data for one or multiple load cells
    
    Args:
        dout_pin(int or [int]): Raspberry Pi GPIO pins where data from HX711 is received
        sck_pin(int): Raspberry Pi clock output pin where sck signal to HX711 is sent
        gain_channel_A(int or [int]): Optional, by default value 128. Options (128 || 64)
        select_channel(str or [str]): Optional, by default 'A'. Options ('A' || 'B')

    Raises:
        TypeError:
            if dout_pins not an int or list of ints
            if gain_channel_A or select_channel not match equired values
    """
    
    def __init__(self,
                 dout_pins,
                 sck_pin: int,
                 channel_A_gains = None,
                 channel_selects = None,
                 ):
        
        self.set_dout_pins(dout_pins)
        self.set_sck_pin(sck_pin)
        self.set_channel_a_gains(channel_A_gains)
        self.set_channel_selects(channel_selects)
        self.init_load_cells()
        self.init_gpio()
                
    def set_dout_pins(self, dout_pins):
        # set dout_pins as array of ints. If just an int input, turn it into a single array of int
        self.dout_pins = convert_to_list(dout_pins, _type=int, _default_output=None)
        if self.dout_pins is None:
            # raise error if pins not set properly
            raise TypeError(f'dout_pins must be type int or array of int.\nReceived dout_pins: {dout_pins}')
        
    def set_sck_pin(self, sck_pin):
        # set sck_pin if int
        if type(sck_pin) is not int:
            raise TypeError(f'sck_pin must be type int.\nReceived sck_pin: {sck_pin}')
        self.sck_pin = sck_pin
        
    def set_channel_a_gains(self, channel_A_gains):
        # check gain channels for type and value. Default is 128 if None
        self.channel_A_gains = convert_to_list(channel_A_gains, _type=int, _default_output=[128]*len(self.dout_pins))
        if not all([x in [128,64] for x in self.channel_A_gains]):
            # raise error if gain channel(s) not 128 or 64
            raise TypeError(f'channel_A_gains must be 128 or 64.\nReceived channel_A_gains: {channel_A_gains}')
        if len(self.channel_A_gains) < len(self.dout_pins):
            self.channel_A_gains = self.channel_A_gains + [128]*(len(self.dout_pins)-len(self.channel_A_gains))
        
    def set_channel_selects(self, channel_selects):
        # check select channels for type and value. Default is A if None
        self.select_channel_list = convert_to_list(channel_selects, _type=str, _default_output=['A']*len(self.dout_pins))
        if not all([x in ['A','B'] for x in self.select_channel_list]):
            # raise error if channel(s) not A or B
            raise TypeError(f'channel_selects must be A or B.\nReceived channel_selects: {channel_selects}')
        if len(self.select_channel_list) < len(self.dout_pins):
            self.select_channel_list = self.select_channel_list + ['A']*(len(self.dout_pins)-len(self.select_channel_list))
            
    def init_load_cells(self):
        # initialize load cell instances
        self.load_cells = []
        for (dout_pin, gain_channel_A, select_channel) in zip(self.dout_pins, self.channel_A_gains, self.select_channel_list):
            self.load_cells.append(LoadCell(dout_pin, gain_channel_A, select_channel))
            
    def init_gpio(self):
        # init GPIO
        if not SIMULATE_PI:
            GPIO.setup(self.sck_pin, GPIO.OUT)  # sck_pin is output only
            for dout in self.dout_pins:
                GPIO.setup(dout, GPIO.IN)  # dout_pin is input only
            
class LoadCell:
    """
    LoadCell class holds data for one load cell
    """
    
    def __init__(self,
                 dout_pin,
                 gain_channel_A = 128,
                 select_channel = 'A',
                 ):
        self.dout_pin = dout_pin
        self.gain_channel_A = gain_channel_A
        self.select_channel = select_channel
        self._offset = 0.
        self._last_raw_data = 0.
        self._scale_ratio = 1.
        self._debug_mode = False
        