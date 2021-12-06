# hx711-multi

[![Publish to PyPI](https://github.com/morrious/hx711-multi/actions/workflows/python-publish.yml/badge.svg)](https://pypi.org/project/hx711-multi/) [![Downloads](https://pepy.tech/badge/hx711-multi)](https://pepy.tech/project/hx711-multi)

HX711 class to sample a 24-bit ADC (or multiple) with Python 3 on a Rasperry Pi Zero, 3 or 4

## Description

This library allows the user to configure and read from one or multiple HX711 ADCs with a Raspberry Pi. It was developed and tested in Python 3.8 on Raspberry Pi 4B with Raspberry Pi OS Lite v5.10.

Capabilities:

- Configure Raspberry Pi digital pins for reading measurements
- Configure Raspberry Pi SCK pin, or clock pin, used for configuring channel and triggering measurements
- Configure Channel (A | B)
- Configure Channel A Gain (128 | 64)
- Power down ADC
- Power up ADC
- Zero ADC at start
- Configure individual weight multiples for calibration of each scale to real-world weight
- Read raw measurements from ADCs
- Read weight measurements from ADCs

**This package requires RPi.GPIO to be installed in Python 3.**

## Hardware

General HX711 documentation is included in Docs folder.

The default sample rate of the HX711 is 10Hz, unless you wire the power to the RATE pin (15), at which point you can sample at 80Hz. I've included a picture of this wiring if desired. The SparkFun board includes a jumper option for this.

[SparkFun Hookup Guide](https://learn.sparkfun.com/tutorials/load-cell-amplifier-hx711-breakout-hookup-guide) - great resource for understanding the wiring to your HX711

[SparkFun Load Cells Guide](https://learn.sparkfun.com/tutorials/getting-started-with-load-cells) - great resource for understanding load cells

## Getting started

Install with `pip3 install hx711_multi`

**Basic usage example:**

_(also found at /tests/simple_read_test.py)_

```python
#!/usr/bin/env python3

from hx711_multi import HX711
from time import perf_counter
import RPi.GPIO as GPIO  # import GPIO

# init GPIO (should be done outside HX711 module in case you are using other GPIO functionality)
GPIO.setmode(GPIO.BCM)  # set GPIO pin mode to BCM numbering

readings_to_average = 10
sck_pin = 1
dout_pins = [2, 3, 4, 14, 15]
weight_multiples = [-5176, -5500, -5690, -5484, -5455]

# create hx711 instance
hx711 = HX711(dout_pins=dout_pins,
              sck_pin=sck_pin,
              channel_A_gain=128,
              channel_select='A',
              all_or_nothing=False,
              log_level='CRITICAL')
# reset ADC, zero it
hx711.reset()
try:
    hx711.zero(readings_to_average=readings_to_average*3)
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
        sample_rate = readings_to_average/read_duration
        print('\nread duration: {:.3f} seconds, rate: {:.1f} Hz'.format(read_duration, sample_rate))
        print(
            'raw',
            ['{:.3f}'.format(x) if x is not None else None for x in raw_vals])
        print(' wt',
              ['{:.3f}'.format(x) if x is not None else None for x in weights])
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
```

**Calibration sequence**

Each HX711 ADC needs to be calibrated separately in order to account for variance in raw measurements compared to real world weight. For example, the ADC may return a value of 5000 which corresponds to 1 gram. In this case, the weight multiple for this ADC should be set to 5000.

Run the calibration sequence with known weights after initializing your HX711 object with the below command. Optional input for known weights included so that you can run through the process faster without needing to type in the weights throughout the sequence. If no known weights are input, it will prompt user before each measurement. This should only need to be performed once during hardware setup, or if the measurement environment changes (temperature, humidity, etc).

_(full example can be found at /tests/calibrate.py)_

```python
weight_multiple = hx711.run_calibration(known_weights=[5, 10, 50, 100])
print(f'Weight multiple = {weight_multiple}')
```

## Author

- James Morris (https://james.pizza)

## License

- Free software: MIT license

## Credits

- Starting point: https://github.com/gandalf15/HX711/
