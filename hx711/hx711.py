
#!/usr/bin/env python3
"""
This file holds HX711 class and LoadCell class which is used within HX711 in order to track multiple load cells
"""

from hx711.utils import convert_to_list

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
                 gain_channel_A = None,
                 select_channel = None,
                 ):
        
        # set dout_pins as array of ints. If just an int input, turn it into a single array of int
        self.dout_pins = convert_to_list(dout_pins, _type=int, _default_output=None)
        if self.dout_pins is None:
            # raise error if pins not set properly
            raise TypeError(f'dout_pins must be type int or array of int.\nReceived dout_pins: {dout_pins}')
        # set sck_pin if int
        if type(sck_pin) is not int:
            raise TypeError(f'sck_pin must be type int.\nReceived sck_pin: {sck_pin}')
        self.sck_pin = sck_pin
        # check gain and select channels for type and value. Default is 128 and A if None
        self.gain_channel_A = convert_to_list(gain_channel_A, _type=int, _default_output=[128]*len(self.dout_pins))
        if not all([x in [128,64] for x in self.gain_channel_A]):
            # raise error if gain channel(s) not 128 or 64
            raise TypeError(f'gain_channel_A must be 128 or 64.\nReceived gain_channel_A: {gain_channel_A}')
        if len(self.gain_channel_A) < len(self.dout_pins):
            self.gain_channel_A = self.gain_channel_A + [128]*(len(self.dout_pins)-len(self.gain_channel_A))
        self.select_channel = convert_to_list(select_channel, _type=str, _default_output=['A']*len(self.dout_pins))
        if not all([x in ['A','B'] for x in self.select_channel]):
            # raise error if channel(s) not A or B
            raise TypeError(f'select_channel must be A or B.\nReceived select_channel: {select_channel}')
        if len(self.select_channel) < len(self.dout_pins):
            self.select_channel = self.select_channel + ['A']*(len(self.dout_pins)-len(self.select_channel))