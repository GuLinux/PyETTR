#!/usr/bin/env python3
import time
import numpy as np
import sys
from ettr import ETTRSingleRange, ETTRISORange, ETTRDualRange, ExposureToTheRight, ettr_dual_range, ettr_iso_range, ettr_single_range, logger as ettr_logger
import logging

ettr_logger.addHandler(logging.StreamHandler())
ettr_logger.setLevel(logging.DEBUG)


def get_next_value_linear(exposure):
    return 10 + (exposure/10 * 255)

@ettr_single_range(0.001, 10)
def capture_exposure(exposure, options={}):
    next_value = get_next_value_linear(exposure)
    next_value = int(max(1, min(next_value, 255)))
    print(f'@@@@@@@@@@@@@ Exposure: {exposure}, next_value={next_value}')
    return [next_value] * 10

# iso = ETTRISORange(capture_iso, [100, 200, 400, 800])
# exp = ETTRSingleRange(capture_exposure, 0.001, 10)
# dual = ETTRDualRange(capture_f, exp, iso, 0.8, labels=('exposure', 'ISO'))
ettr = ExposureToTheRight(capture_exposure) 

while True:
    ettr.capture(1, timelapse_sleep=2)
    # ettr_dual()
