#!/usr/bin/env python3

# try to import hx711, first from src dir, second from src dir after adding parent to path, last from pip
try:
    from src.hx711_multi import HX711
except:
    try:
        # try after inserting parent folder in path
        import sys
        import pathlib
        from os.path import abspath
        sys.path.insert(0, str(pathlib.Path(abspath(__file__)).parents[1]))
        from src.hx711_multi import HX711
    except:
        from hx711_multi import HX711

from time import perf_counter

import board
import busio
import digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017

readings_to_average = 10
sck_pin = 1
dout_pins = [2]
weight_multiples = [1]

# initialize MCP
i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c)  # MCP23017
mcp = MCP23017(i2c, address=0x20)  # MCP23017 A0,A1,A2 not set


# create custom functions for init, write, read
def mcp_init_gpio_func(sck_pin, dout_pins):
    # init clock/sck pin
    mcp_sck_pin = mcp.get_pin(sck_pin)
    mcp_sck_pin.switch_to_output(value=True)
    # init dout pins
    for dout in dout_pins:
        mcp_dout_pin = mcp.get_pin(dout)
        # mcp_dout_pin.direction = digitalio.Direction.INPUT
        # mcp_dout_pin.pull = digitalio.Pull.UP
        mcp_dout_pin.switch_to_input(pull=digitalio.Pull.UP)


def mcp_gpio_output_func(pin_number, value=False):
    mcp_output_pin = mcp.get_pin(pin_number)
    mcp_output_pin.value = value


def mcp_gpio_input_func(pin_number):
    mcp_output_pin = mcp.get_pin(pin_number)
    return mcp_output_pin.value


# create hx711 instance
hx711 = HX711(
    dout_pins=dout_pins,
    sck_pin=sck_pin,
    channel_A_gain=128,
    channel_select='A',
    all_or_nothing=False,
    log_level='CRITICAL',
    init_gpio_func=mcp_init_gpio_func,
    gpio_output_func=mcp_gpio_output_func,
    gpio_input_func=mcp_gpio_input_func,
)
# reset ADC, zero it
hx711.reset()
try:
    hx711.zero(readings_to_average=readings_to_average * 3)
except Exception as e:
    print(e)
# uncomment below loop to see raw 2's complement and read integers
# for adc in hx711._adcs:
#     print(adc.raw_reads)  # these are the 2's complemented values read bitwise from the hx711
#     print(adc.reads)  # these are the raw values after being converted to signed integers
hx711.set_weight_multiples(weight_multiples=weight_multiples)

# read until keyboard interrupt
try:
    while True:
        start = perf_counter()

        # perform read operation, returns signed integer values as delta from zero()
        # readings aare filtered for bad data and then averaged
        raw_vals = hx711.read_raw(readings_to_average=readings_to_average)

        # request weights using multiples set previously with set_weight_multiples()
        # This function call will not perform a new measurement, it will just use what was acquired during read_raw()
        weights = hx711.get_weight()

        read_duration = perf_counter() - start
        sample_rate = readings_to_average / read_duration
        print('\nread duration: {:.3f} seconds, rate: {:.1f} Hz'.format(read_duration, sample_rate))
        print('raw', ['{:.3f}'.format(x) if x is not None else None for x in raw_vals])
        print(' wt', ['{:.3f}'.format(x) if x is not None else None for x in weights])
        # uncomment below loop to see raw 2's complement and read integers
        # for adc in hx711._adcs:
        #     print(adc.raw_reads)  # these are the 2's complemented values read bitwise from the hx711
        #     print(adc.reads)  # these are the raw values after being converted to signed integers
except KeyboardInterrupt:
    print('Keyboard interrupt..')
except Exception as e:
    print(e)
