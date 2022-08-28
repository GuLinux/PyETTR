#!/usr/bin/env python3
import time
import numpy as np
import sys
from ettr import ETTRSingleRange, ETTRISORange, ETTRDualRange, ExposureToTheRight, ettr_dual_range, ettr_iso_range, ettr_single_range, logger as ettr_logger
import logging

ettr_logger.addHandler(logging.StreamHandler())
ettr_logger.setLevel(logging.INFO)

numbers = [1]
if len(sys.argv) > 1:
    numbers = [int(n) for n in sys.argv[1:]]


def get_shoot_array():
    global numbers
    current_number = numbers[0]
    numbers = numbers[1:]
    numbers.append(current_number)
    print(f'current number: {current_number}, numbers: {numbers}')
    return np.array([current_number] * 10)

# @ettr(tolerance=0.02, percentile=0.90, max_percentile_value=0.90, timelapse_sleep=2)
@ettr_dual_range(isos=[100, 200, 400, 800], min_value=0.001, max_value=10, labels=('Exposure', 'ISO'))
def ettr_dual(exposure, iso, options={}):
    print(f'@@@@@@@@@@@@@ Dual: Exposure: {exposure}, ISO={iso}')
    return get_shoot_array()

@ettr_single_range(0.001, 10)
def capture_exposure(exposure, options={}):
    print(f'@@@@@@@@@@@@@ Exposure: {exposure}')
    return get_shoot_array()

@ettr_iso_range([100, 200, 400, 800])
def capture_iso(iso, options={}):
    print(f'@@@@@@@@@@@@@ ISO: {iso}')
    return get_shoot_array()

# iso = ETTRISORange(capture_iso, [100, 200, 400, 800])
# exp = ETTRSingleRange(capture_exposure, 0.001, 10)
# dual = ETTRDualRange(capture_f, exp, iso, 0.8, labels=('exposure', 'ISO'))
ettr = ExposureToTheRight(ettr_dual, percentile=0.90, max_percentile_value=0.90) 

while True:
    ettr.capture(1, timelapse_sleep=2)
    # ettr_dual()
