# hx711-multi

HX711 class to sample 24-bit ADCs with Python 3 on a Raspberry Pi Rasperry Pi Zero, 2 or 3

Description
-----------
This library allows to configure and read from one or multiple HX711 load cells with a Raspberry Pi. It was developed and tested in Python 3.8 on Raspberry Pi 4B with Raspberry Pi OS Lite v5.10.

Capabilities:

* Configure Raspberry Pi digital pins for reading measurements
* Configure Raspberry Pi SCK pin, or clock pin, used for configuring channel and triggering measurements
* Configure Channel (A | B)
* Configure Channel A Gain (128 | 64)
* Power down load cell
* Power up load cell
* Zero load cell at start
* Configure individual weight multiples for calibration of each scale to real-world weight
* Read raw measurements from load cells
* Read weight measurements from load cells

**This package requires RPi.GPIO to be installed in Python 3.**

Hardware
-----------
Documentation is included in Docs folder. Default rate of HX711 is 10Hz, unless you wire the digital power (DVDD) to the RATE pin (15), at which point you can sample at 80Hz. I've included a picture of this wiring if desired.

Getting started
---------------

Install with ```pip3 install hx711multi```

Basic usage example:

```python
    #!/usr/bin/env python3

    import RPi.GPIO as GPIO  # import GPIO
    from hx711_multi_ import HX711
    from time import sleep, perf_counter

    #init GPIO (should be done outside HX711 module in case you are using other GPIO functionality)
    GPIO.setmode(GPIO.BCM)  # set GPIO pin mode to BCM numbering

    dout_pins = [13,21,16,26,19]
    sck_pin = 20
    weight_multiples = [4489.80, 4458.90, 4392.80, 1, -5177.15]

    hx711 = HX711(dout_pins=dout_pins, sck_pin=sck_pin, all_or_nothing=False, log_level='CRITICAL')  # create an object
    hx711.power_down()
    hx711.power_up()
    hx711.zero()
    hx711.set_weight_multiples(weight_multiples=weight_multiples)

    # read until keyboard interrupt
    try:
        while True:
            start = perf_counter()
            raw_vals = hx711.read_raw(readings_to_average=5)
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
```

Author
-------
* [James Morris](https://morrisjam.es)

License
-------
* Free software: MIT license

Credits
---------
https://github.com/gandalf15/HX711/ as base starting point