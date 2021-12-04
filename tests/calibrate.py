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

from statistics import mean, stdev
import RPi.GPIO as GPIO  # import GPIO

# init GPIO (should be done outside HX711 module in case you are using other GPIO functionality)
GPIO.setmode(GPIO.BCM)  # set GPIO pin mode to BCM numbering

averaging_count = 10  # datapoints to read per measurement

# set values using python input args
# arg 1: SCK/Clock pin
# arg 2: DOut/Measurement pin
# args 3+: known weights to use for calibration
sck_pin = None
dout_pin = None
known_weights = []
if len(sys.argv) > 1:
    sck_pin = int(sys.argv[1])
    if len(sys.argv) > 2:
        dout_pin = int(sys.argv[2])
    if len(sys.argv) > 3:
        known_weights = [float(x) for x in sys.argv[3:]]

# prompt for pin inputs if not entered as args
if sck_pin is None:
    sck_pin = input('Enter SCK/Clock pin: ')
    if not sck_pin:
        print('No SCK/Clock pin entered. Exiting..')
        quit()
    else:
        sck_pin = int(sck_pin)
if dout_pin is None:
    dout_pin = input('Enter DOut/Measurement pin: ')
    if not dout_pin:
        print('No DOut/Measurement pin entered. Exiting..')
        quit()
    else:
        dout_pin = int(dout_pin)

# if known weights were entered, speed up script by not prompting user to prepare
if not known_weights:
    input('Remove all weight from scale and press any key to continue..')

try:
    # create hx711 instance
    hx711 = HX711(dout_pins=dout_pin,
                  sck_pin=sck_pin,
                  channel_A_gain=128,
                  channel_select='A',
                  all_or_nothing=False,
                  log_level='CRITICAL')

    # reset ADC, zero it, set weight multiple to 1
    hx711.reset()
    hx711.zero(readings_to_average=averaging_count)
    hx711.set_weight_multiples(weight_multiples=1)

    # loop until no more known weights or user has not supplied a known weight input
    weights_known = []
    weights_measured = []
    loop = True
    i = 0
    while loop:
        # if known weights entered as args, set wt_known to this and prompt user to place weight on scale
        if i < len(known_weights):
            wt_known = known_weights[i]
            input(f'Place {wt_known} on scale and press enter to continue..')
        else:
            # if weights entered as args, but current index is past last known, set wt_known to None to end loop
            # else, prompt user for next known weight
            if known_weights:
                wt_known = None
            else:
                wt_known = input(
                    'Place known weight on scale. Enter this known weight (enter nothing to end): ')
        # if wt_known has been entered or from args, perform measurement
        # else, end loop
        if wt_known:
            wt_known = float(wt_known)
            # try 3 times to get measurement
            for _ in range(3):
                try:
                    wt_measured = hx711.read_raw(
                        readings_to_average=averaging_count)
                except:
                    pass
                if wt_measured:
                    break
            wt_measured = float(wt_measured)
            weights_known.append(wt_known)
            weights_measured.append(wt_measured)
            try: ratio = round(wt_measured / wt_known, 1)
            except: ratio = 1
            print(
                f'measurement/known = {round(wt_measured,1)}/{round(wt_known,1)} = {ratio}')
        else:
            loop = False
        i += 1

    # if known weights and measured weights, calculate multiples for each and print the data
    if weights_known and weights_measured:
        calculated_multiples = [measured / known for known,
                                measured in zip(weights_known, weights_measured)]
        if len(calculated_multiples) > 1:
            multiples_stdev = round(stdev(calculated_multiples), 0)
            weight_multiple = round(mean(calculated_multiples), 1)
        else:
            multiples_stdev = 0
            weight_multiple = round(calculated_multiples[0], 1)
        print(
            f'\nScale ratio with {len(weights_known)} samples: {weight_multiple}  |  stdev = {multiples_stdev}')
    else:
        print('\nno measurements taken')

except KeyboardInterrupt:
    print('Keyboard interrupt..')
except Exception as e:
    print(e)

# cleanup GPIO
GPIO.cleanup()
