import psutil
from time import time

from Catascopia.Probe import Probe
from Catascopia.Metrics import SimpleMetric

# use pid param if the monitored process different from the current process

class ProcessProbe(Probe):

    __PROC_TIMESTEP__ = 0.2

    def __init__(self, name = "ProcessProbe", periodicity = 5, pid = None):
        super(ProcessProbe, self).__init__(name, periodicity)

        self.cpu_percent = SimpleMetric('cpu_percent', '%', 'process-level cpu utilization', minVal=0, higherIsBetter=False)
        self.cpu_time = SimpleMetric('cpu_time', 's', 'process-level cpu time', minVal=0, higherIsBetter=False)
        self.io_time = SimpleMetric('io_time', 's', 'process-level io time (linux-only)', minVal=0, higherIsBetter=False)
        self.alive_time = SimpleMetric('alive_time', 's', 'time process is alive', minVal=0, higherIsBetter=False)
        self.probe_alive_time = SimpleMetric('probe_alive_time', 's', 'time probe is alive', minVal=0, higherIsBetter=False)

        self.add_metric(self.cpu_percent)
        self.add_metric(self.cpu_time)
        self.add_metric(self.io_time)
        self.add_metric(self.alive_time)
        self.add_metric(self.probe_alive_time)

        self.proc = psutil.Process(pid)
        self.col_start = time()

    def get_desc(self):
        return "ProcessProbe collects process-level utilization metrics..."

    def collect(self):
        self.cpu_percent.set_val(self.proc.cpu_percent(interval=ProcessProbe.__PROC_TIMESTEP__))
        # user+sys including child threads
        ct = self.proc.cpu_times()
        self.cpu_time.set_val(sum(ct[:4]))
        try:
           self.io_time.set_val(ct[4])
        except IndexError:
            pass # not a Linux OS, so no io_time counter

        self.alive_time.set_val(time() - self.proc.create_time())
        self.probe_alive_time.set_val(time() - self.col_start)

def main():
    p = ProcessProbe()
    p.set_debugmode(True)
    p.set_logging()
    p.activate()

if __name__ == "__main__":
    main()