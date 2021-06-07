#!/usr/bin/env python3

from hx711_multi import HX711
from time import perf_counter
import RPi.GPIO as GPIO  # import GPIO

#init GPIO (should be done outside HX711 module in case you are using other GPIO functionality)
GPIO.setmode(GPIO.BCM)  # set GPIO pin mode to BCM numbering

dout_pins = [13,21,16,26,19]
sck_pin = 20
weight_multiples = [4489.80, 4458.90, 4392.80, 1, -5177.15]

hx711 = HX711(dout_pins=dout_pins, sck_pin=sck_pin, all_or_nothing=False, log_level='CRITICAL')  # create an object
hx711.reset()
hx711.zero()
hx711.set_weight_multiples(weight_multiples=weight_multiples)

# read until keyboard interrupt
try:
    while True:
        start = perf_counter()
        raw_vals = hx711.read_raw(readings_to_average=10)
        weights = hx711.read_weight(use_prev_read=True)
        read_duration = perf_counter() - start
        print('\nread duration: {:.3f} seconds'.format(read_duration))
        print('raw', ['{:.3f}'.format(x) if x is not None else None for x in raw_vals])
        print(' wt', ['{:.3f}'.format(x) if x is not None else None for x in weights])
except KeyboardInterrupt:
    print('Keyboard interrupt..')
except Exception as e:
    print(e)

# cleanup GPIO
GPIO.cleanup()