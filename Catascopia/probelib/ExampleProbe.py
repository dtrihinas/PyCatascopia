import random
from Catascopia.Probe import Probe
from Catascopia.Metrics import SimpleMetric, CounterMetric, DiffMetric

class ExampleProbe(Probe):

    def __init__(self, name = "ExampleProbe", periodicity = 5):
        super(ExampleProbe, self).__init__(name, periodicity)

        self.myMetric1 = SimpleMetric('myMetric1', '%', 'random double between 0 and 10', 0, 10)
        self.myMetric2 = SimpleMetric('myMetric2', '#', 'random int between 0 and 1000', 0, 1000, higherIsBetter=False)
        self.myMetric3 = CounterMetric('myMetric3', '#', 'counter incrementing by 1 and reseting at 20', maxVal=20)
        self.myMetric4 = DiffMetric('myMetric4', '#', 'scaled difference from previous val')

        self.add_metric(self.myMetric1)
        self.add_metric(self.myMetric2)
        self.add_metric(self.myMetric3)
        self.add_metric(self.myMetric4)

    def get_desc(self):
        return "ExampleProbe collects some dummy metrics..."

    def collect(self):
        d = random.uniform(0, 10)
        i = random.randint(0, 1000)

        self.myMetric1.set_val(d)
        self.myMetric2.set_val(i)
        self.myMetric3.inc()
        self.myMetric4.update(i)


def main():
    p = ExampleProbe()
    p.set_debugmode(True)
    p.set_logging()
    p.activate()

if __name__ == "__main__":
    main()