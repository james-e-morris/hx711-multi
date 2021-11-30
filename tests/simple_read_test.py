#!/usr/bin/env python3

# set root dir if being run standlone from subfolder
if __name__ == '__main__':
    import sys
    import pathlib
    from os.path import abspath
    # set root dir as 1 directories up from here
    ROOT_DIR = str(pathlib.Path(abspath(__file__)).parents[1])
    sys.path.insert(0, ROOT_DIR)

from src.hx711_multi import HX711
from time import perf_counter
import RPi.GPIO as GPIO  # import GPIO

# init GPIO (should be done outside HX711 module in case you are using other GPIO functionality)
GPIO.setmode(GPIO.BCM)  # set GPIO pin mode to BCM numbering

dout_pins = [13, 21, 16, 26, 19]
sck_pin = 20
weight_multiples = [4489.80, 4458.90, 4392.80, 1, -5177.15]

# create hx711 instance
hx711 = HX711(dout_pins=dout_pins,
              sck_pin=sck_pin,
              all_or_nothing=False,
              log_level='CRITICAL')
# reset ADC, zero it
hx711.reset()
try:
    hx711.zero(readings_to_average=30)
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
        raw_vals = hx711.read_raw(readings_to_average=10)

        # request weights using multiples set previously with set_weight_multiples()
        # use_prev_read=True means this function call will not perform a new read, it will use what was acquired during read_raw()
        weights = hx711.read_weight(use_prev_read=True)

        read_duration = perf_counter() - start
        print('\nread duration: {:.3f} seconds'.format(read_duration))
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

# cleanup GPIO
GPIO.cleanup()
