import psutil

from Catascopia.Probe import Probe
from Catascopia.Metrics import SimpleMetric

class ProcessProbe(Probe):

    __PROC_TIMESTEP__ = 0.2

    def __init__(self, name = "ProcessProbe", periodicity = 5):
        super(ProcessProbe, self).__init__(name, periodicity)
        self.cpu_percent = SimpleMetric('cpu_percent', '%', 'process-level cpu utilization', minVal=0, higherIsBetter=False)
        self.add_metric(self.cpu_percent)
        self.proc = psutil.Process()

    def get_desc(self):
        return "ProcessProbe collects process-level utilization metrics..."

    def collect(self):
        self.cpu_percent.set_val(self.proc.cpu_percent(interval=ProcessProbe.__PROC_TIMESTEP__))

def main():
    p = ProcessProbe()
    p.set_debugmode(True)
    p.set_logging()
    p.activate()

if __name__ == "__main__":
    main()