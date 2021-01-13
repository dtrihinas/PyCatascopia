import time


class Metric(object):

    def __init__(self, name, units, desc):
        self.name = name
        self.units = units
        self.desc = desc
        self.val = None
        self.timestamp = None
        self.group = None

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_units(self):
        return self.units

    def set_units(self, units):
        self.units = units

    def get_desc(self):
        return self.desc

    def set_desc(self, desc):
        self.desc

    def get_timestamp(self):
        return self.timestamp

    def set_timestamp(self, timestamp):
        self.timestamp

    def get_val(self):
        return self.val

    def set_val(self, val):
        self.val = val

    def get_group(self):
        return self.group

    def set_group(self, group):
        self.group = group

    def to_dict(self):
        d = dict()
        d['name'] = self.name
        d['units'] = self.units
        d['desc'] = self.desc
        d['timestamp'] = self.timestamp
        d['val'] = self.val
        d['group'] = self.group
        return d

    def __str__(self):
        return str(self.to_dict())


class SimpleMetric(Metric):

    def __init__(self, name, units, desc, minVal = float('-inf'), maxVal = float('inf'), higherIsBetter=True):
        super(SimpleMetric, self).__init__(name, units, desc)
        self.higherIsBetter = higherIsBetter
        self.minVal = minVal
        self.maxVal = maxVal

    def get_higherisbetter(self):
        return self.higherIsBetter

    def set_higherisbetter(self, higherIsBetter):
        self.higherIsBetter = higherIsBetter

    def get_minval(self):
        return self.minVal

    def set_minval(self, minVal):
        self.minVal = minVal

    def get_maxval(self):
        return self.maxVal

    def set_maxval(self, maxVal):
        self.maxVal = maxVal

    def set_val(self, val):
        self.timestamp = int(time.time())
        self.val = val

    def __str__(self):
        m = super().to_dict()
        m['higherIsBetter'] = self.higherIsBetter
        m['minVal'] = self.minVal
        m['maxVal'] = self.maxVal
        return str(m)

class CounterMetric(SimpleMetric):
    def __init__(self, name, units, desc, minVal = 0, maxVal = float('inf'), higherIsBetter=True, step=1, reset=True):
        super(CounterMetric, self).__init__(name, units, desc, minVal, maxVal, higherIsBetter)
        self.step = step
        self.counter = minVal
        self.reset = reset

    def inc(self):
        self._inc(self.step)

    def _inc(self, step):
        if isinstance(step, int):
            self.counter += step
            if self.counter > self.maxVal:
                if self.reset:
                    self.counter = self.minVal
                else:
                    raise CatascopiaMetricValueException('CounterMetric ' + self.name + ' counter max value overflow')
            self.set_val(self.counter)
        else:
            raise CatascopiaMetricValueException('CounterMetric ' + self.name + ' step ' + step + ' is not an integer')


class DiffMetric(SimpleMetric):

    def __init__(self, name, units='%', desc='a diff metric', minVal = float('-inf'), maxVal = float('inf'), higherIsBetter=True):
        super(DiffMetric, self).__init__(name, units, desc, minVal, maxVal, higherIsBetter)
        self.prev = 0
        self.cur = 0
        self.diff = 0

    def update(self, val):
        self.prev = self.cur
        self.cur = val
        try:
            self.diff = (self.cur - self.prev)/self.prev
        except TypeError:
            raise CatascopiaMetricValueException('DiffMetric ' + self.name + ' value type ' + str(type(val))
                                                 + ' incompatible, expected numeric value')
        except ZeroDivisionError:
            self.diff = 0
        self.set_val(self.diff * 100)

# TODO implement TimerMetric class
class TimerMetric(Metric):
    pass


class CatascopiaMetricValueException(Exception):
    pass