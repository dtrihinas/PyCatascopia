import time
import threading

class Metric(object):

    def __init__(self, name, units, desc, minVal = None, maxVal = None, higherIsBetter=True):
        self.name = name
        self.units = units
        self.desc = desc
        self.higherIsBetter = higherIsBetter
        self.minVal = minVal
        self.maxVal = maxVal
        self.group = None
        self.val = None
        self.timestamp = None

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

    def to_dict(self):
        d = dict()
        d['name'] = self.name
        d['units'] = self.units
        d['desc'] = self.desc
        d['timestamp'] = self.timestamp
        d['val'] = self.val
        d['higherIsBetter'] = self.higherIsBetter
        d['minVal'] = self.minVal
        d['maxVal'] = self.maxVal
        d['group'] = self.group
        return d

    def __str__(self):
        return str(self.to_dict())


class SimpleMetric(Metric):

    def __init__(self, name, units, desc, minVal = float('-inf'), maxVal = float('inf'), higherIsBetter=True):
        super(SimpleMetric, self).__init__(name, units, desc, minVal, maxVal, higherIsBetter)

    def set_val(self, val):
        self.timestamp = int(time.time())
        self.val = val


class CounterMetric(SimpleMetric):
    def __init__(self, name, units, desc, minVal = 0, maxVal = float('inf'), higherIsBetter=True, step=1, reset=True):
        super(CounterMetric, self).__init__(name, units, desc, minVal, maxVal, higherIsBetter)
        self.step = step
        self.counter = minVal
        self.reset = reset

    def inc(self):
        self.inc_with_step(self.step)

    def inc_with_step(self, step):
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


#TODO add some exceptions
class TimerMetric(SimpleMetric):

    IDLE, STARTED, PAUSED, FINISHED = range(4)

    # maxVal is the max time the timer will wait each time before returning a value, default 24hours
    # ensures timer not blocking forever
    def __init__(self, name, units='s', desc='a timer metric', minVal=0, maxVal=86400, higherIsBetter=False):
        super(TimerMetric, self).__init__(name, units, desc, minVal, maxVal, higherIsBetter)
        self.tstart = 0;
        self.tval = 0
        self.timer = None
        self.timer_status = TimerMetric.IDLE

    def timer_start(self):
        if self.timer_status == TimerMetric.IDLE or self.timer_status == TimerMetric.PAUSED:
            self.timer = threading.Timer(0.0, self._waiting_clock_expire, [self.maxVal])
            self.tstart = time.time()
            self.timer.start()
            self.timer_status = TimerMetric.STARTED
            return True
        return False

    def timer_pause(self):
        if self.timer_status == TimerMetric.STARTED:
            self.tval += time.time() - self.tstart
            self.timer.cancel()
            self.timer_status = TimerMetric.PAUSED
            self.set_val(self.tval)
            return True
        return False

    def timer_end(self):
        if self.timer_status == TimerMetric.STARTED:
            self.tval += time.time() - self.tstart
        if self.timer_status == TimerMetric.STARTED or self.timer_status == TimerMetric.PAUSED:
            self.set_val(self.tval)
            if self.timer:
                self.timer.cancel()
            self.timer_status = TimerMetric.FINISHED
            print(self.val)
            return True
        return False

    def timer_reset(self):
        self.timer_status = TimerMetric.IDLE
        self.tval = 0
        self.tstart = 0
        if self.timer:
            self.timer.cancel()
        self.timer = None
        return True

    def timer_reset_and_start(self):
        r = self.timer_reset()
        s = self.timer_start()
        return r and s

    def _waiting_clock_expire(self, max_wait_time):
        time.sleep(max_wait_time)
        self.timer_end()


class CatascopiaMetricValueException(Exception):
    pass