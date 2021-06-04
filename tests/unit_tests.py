#!/usr/bin/env python3
# https://docs.python.org/3/library/unittest.html

if __name__ == '__main__':
    import sys, pathlib
    from os.path import abspath
    ROOT_DIR = str(pathlib.Path(abspath(__file__)).parents[1])  # set root root dir as 1 directories up from here
    sys.path.insert(0, ROOT_DIR)

import unittest
from hx711.hx711 import HX711

class TestStringMethods(unittest.TestCase):

    def test_hx711_inputs(self):
        # check to make sure good inputs work
        good = HX711([1,2,3], 4, [128, 128, 64], ['A', 'B', 'A'])
        self.assertIsInstance(good, HX711)
        # check that it fails with bad dout_pins
        self.assertRaises(TypeError, HX711, [1,2,False], 4, [128, 128, 64], ['A', 'B', 'A'])
        # check that it fails with bad sck_pin
        self.assertRaises(TypeError, HX711, [1,2,3], False, [128, 128, 64], ['A', 'B', 'A'])

if __name__ == '__main__':
    unittest.main()