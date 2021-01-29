import os
import json
from functools import wraps
from time import time, sleep
from random import randint

from Catascopia.Metrics import Metric, SimpleMetric

class CatascopiaDecorators:

    @classmethod
    def timeit(cls, f):
        @wraps(f)
        def wrap(*args, **kw):
            ts = time()
            result = f(*args, **kw)
            te = time()
            name, unit, desc = "time__%s" % (f.__name__), 's', 'Execution duration from %s' % (f.__name__)
            simple_metric = SimpleMetric(name, unit, desc, minVal=0.0, higherIsBetter=False)
            simple_metric.set_val(te - ts)
            cls.__store(simple_metric)
            print(simple_metric.get_val())
            return result
        return wrap

    @classmethod
    def __store(cls, metric: Metric,
                fpath='.'+os.sep + 'time_decorated_metrics.jsonl', fmode='a', encoding='utf-8', format='json'):
        with open(fpath, mode=fmode, encoding=encoding) as file:
            if format == 'json':
                s = json.dumps(metric.to_dict()) + os.linesep
            else:
                s = str(metric) + os.linesep
            file.write(s)


@CatascopiaDecorators.timeit
def intensive_workload_function():
    sleep(randint(1, 10))


def main():

    intensive_workload_function()


if __name__ == "__main__":
    main()

