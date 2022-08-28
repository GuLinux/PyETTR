import numpy
import math
import time
import logging
from functools import wraps


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class ETTRSingleRange:
    def __init__(self, capture_f, minimum_value, maximum_value, step=0):
        self.capture_f = capture_f
        self.minimum_value = minimum_value
        self.maximum_value = maximum_value
        self.step = step

    def __round_to_step(self, n):
        return n if not self.step else math.floor(n/self.step) * self.step

    def calculate(self, ettr):
        return self.__round_to_step(self.minimum_value + (self.maximum_value - self.minimum_value) * ettr)

    def capture(self, ettr, options={}):
        exposure = self.calculate(ettr)
        logger.info(f'Capturing with exposure={exposure}')
        return self.capture_f(exposure, options=options)


class ETTRISORange:
    def __init__(self, capture_f, ISOs):
        self.capture_f = capture_f
        self.ISOs = ISOs

    def capture(self, ettr, options={}):
        iso = self.calculate(ettr)
        logger.info(f'Capturing with ISO={iso}')
        return self.capture_f(iso, options=options)

    def calculate(self, ettr):
        index = int((len(self.ISOs)-1) * float(ettr))
        return self.ISOs[index]


class ETTRDualRange:
    def __init__(self, capture_f, first, second, split=0.5, labels=('first', 'second')):
        self.capture_f = capture_f
        self.first = first
        self.second = second
        self.split = split
        self.labels = labels

    def capture(self, ettr, options={}):
        if ettr < self.split:
            second = self.second.calculate(0)
            first = self.first.calculate(self.__normalise(ettr, 0, self.split))
        else:
            first = self.first.calculate(1)
            second = self.second.calculate(self.__normalise(ettr, self.split, 1))
        logger.info(f'Capturing with {self.labels[0]}={first}, {self.labels[1]}={second}')

        return self.capture_f(first, second, options=options)

    def __normalise(self, n, start, end):
        return (n - start) / (end - start)

class ExposureToTheRight:
    def __init__(self, capture_f, tolerance=0.02, window=0.01, target_position=0.95, target_value=0.90, bpp=8, average_frames=50):
        self.capture_f = capture_f
        self.current_value = None
        self.tolerance = tolerance
        self.target_position = target_position
        self.max_value = math.pow(2, bpp)
        self.target_value = self.max_value * target_value
        self.average_frames = average_frames
        self.window = window
        self.ettr_frames = []

    def ettr_ratio(self, image_array):
        quantile_value = numpy.quantile(image_array, self.target_position)
        ratio = quantile_value / self.target_value
        logger.debug(f'{self.target_position} quantile: {quantile_value}, target quantile: {self.target_value}, ratio={ratio:0.5f}')
        return ratio

    def calculate_next_exposure(self, ettr_ratio):
        next_value = (self.current_value / ettr_ratio) if ettr_ratio else 1
        logger.info(f'current_value={self.current_value}, next_value={next_value}, value_ratio={self.current_value/next_value}')
        return max(0, min(1, next_value))

    def capture(self, initial_value, timelapse_sleep=0, options={}):
        if self.current_value is None:
            self.current_value = initial_value
        started = time.time()
        image = self.capture_f(self.current_value, options)

        current_ettr_ratio = self.ettr_ratio(image)
        while len(self.ettr_frames) >= self.average_frames:
            self.ettr_frames = self.ettr_frames[1:]
        self.ettr_frames.append(current_ettr_ratio)

        avg_ettr_ratio = sum(self.ettr_frames) / len(self.ettr_frames)
        next_value = self.calculate_next_exposure(avg_ettr_ratio)

        logger.debug(f'Exposure captured: [{self.current_value}]; ettr computation: [{current_ettr_ratio}], average: [{avg_ettr_ratio}] next exposure value: [{next_value}], last frames: {self.ettr_frames}')

        difference = abs(next_value - self.current_value) / ((next_value + self.current_value)/2)
        logger.debug(f'Difference: {difference}, toleranceFactor: {difference * self.current_value}')

        if difference <= self.window:
            logger.debug(f'Value within main window tolerance')
        else:
            if difference <= self.tolerance and len(self.ettr_frames) == self.average_frames:
                logger.debug(f'Value within tolerance')
            else:
                logger.info(f'Exposure value outside tolerance')
                self.current_value = next_value
                self.ettr_frames = []

        elapsed = time.time() - started
        if elapsed < timelapse_sleep:
            time.sleep(timelapse_sleep - elapsed)



def ettr_single_range(min_value, max_value, step=0):
    def capture_decorator(f):
        @wraps(f)
        def wrapped(ettr_value, options={}):
            ettr_single_range = ETTRSingleRange(f, min_value, max_value, step)
            return ettr_single_range.capture(ettr_value, options)
        return wrapped
    return capture_decorator


def ettr_iso_range(isos):
    def capture_decorator(f):
        @wraps(f)
        def wrapped(ettr_value, options={}):
            ettr_iso_range = ETTRISORange(f, isos)
            return ettr_iso_range.capture(ettr_value, options)
        return wrapped
    return capture_decorator

def ettr_dual_range(isos, min_value, max_value, step=0, split=0.5, labels=('first', 'second')):
    def capture_decorator(f):
        @wraps(f)
        def wrapped(ettr_value, options={}):
            ettr_single_range = ETTRSingleRange(None, min_value, max_value, step)
            ettr_iso_range = ETTRISORange(None, isos)
            ettr_dual_range = ETTRDualRange(f, ettr_single_range, ettr_iso_range, split=split, labels=labels)
            return ettr_dual_range.capture(ettr_value, options)
        return wrapped
    return capture_decorator

