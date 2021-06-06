#!/usr/bin/env python3

# set root dir if being run standlone from subfolder
if __name__ == '__main__':
    import sys, pathlib
    from os.path import abspath
    ROOT_DIR = str(pathlib.Path(abspath(__file__)).parents[1])  # set root dir as 1 directories up from here
    sys.path.insert(0, ROOT_DIR)

import RPi.GPIO as GPIO  # import GPIO
from hx711.hx711 import HX711
from time import sleep, perf_counter

#init GPIO (should be done outside HX711 module in case you are using other GPIO functionality)
GPIO.setmode(GPIO.BCM)  # set GPIO pin mode to BCM numbering


hx711 = HX711(dout_pins=[13,21,16,19], sck_pin=20, log_level='DEBUG')  # create an object
hx711.power_down()
hx711.power_up()
hx711.zero()

# read until keyboard interrupt
try:
    while True:
        start = perf_counter()
        print('raw', hx711.read_raw())  # get raw data reading from hx711
        read_duration = perf_counter() - start
        print('    read duration: {:.3f} seconds'.format(read_duration))
except KeyboardInterrupt:
    print('Keyboard interrupt..')
except Exception as e:
    print(e)

# cleanup GPIO
GPIO.cleanup()