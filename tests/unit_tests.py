#!/usr/bin/env python3
# https://docs.python.org/3/library/unittest.html

import unittest
from hx711_multi import HX711
import RPi.GPIO as GPIO  # import GPIO
GPIO.setmode(GPIO.BCM)  # set GPIO pin mode to BCM numbering

class TestStringMethods(unittest.TestCase):

    def test_hx711_inputs(self):
        # check to make sure good inputs work
        good = HX711([1,2,3], 4, 128, 'A')
        self.assertIsInstance(good, HX711)
        # check that it fails with bad dout_pins
        self.assertRaises(TypeError, HX711, [1,2,False], 4, 128, 'A')
        # check that it fails with bad sck_pin
        self.assertRaises(TypeError, HX711, [1,2,3], False, 128, 'A')

if __name__ == '__main__':
    unittest.main()