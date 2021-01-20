import abc
import time
import os
import logging.handlers
from threading import Thread, Event
from queue import Queue
from uuid import uuid4


class Probe(Thread, metaclass = abc.ABCMeta):

    __DEFAULT_LOGGING_PATH = "."
    __MAX_CONSECUTIVE_ERRORS = 10

    def __init__(self, name, periodicity,  debug = False, logging = False):
        # give the thread the same name with the probe for easier debugging
        super(Probe, self).__init__(name = name)
        # default data collection periodicity in seconds
        self.periodicity = periodicity
        self.probeid = uuid4()
        # probe's data collection initialized as inactive
        self.probestatus = ProbeStatus.INACTIVE
        #DO NOT MESS WITH: threading lock/event handle state transition
        self._activateEvent = Event()
        # flag to test if first time Probe activated
        self._first = True
        # flag to set Probe in debug mode
        self._debug = debug
        # flag to set Probe persistent logging
        self.logging = logging
        self.logger = None
        if self.logging:
            self.set_logging()
        self.metrics = dict()
        # queue to be attached by data consumer
        self.queue = None
        #consecutive error counter
        self.errors = 0

    def set_logging(self, path=None):
        """method that configures logging"""
        self.logger = None
        try:
            logfolder = ''
            if path is None:
                logfolder = Probe.__DEFAULT_LOGGING_PATH
            else:
                logfolder = path
            logfolder += os.sep + 'logs' + os.sep + self.name
            if not os.path.isdir(logfolder):
                os.makedirs(logfolder)
            logfile = logfolder + os.sep + self.name + '.log'
            # Set up a specific logger with our desired output level
            self.logger = logging.getLogger(self.name)
            self.logger.setLevel(logging.INFO)
            # Add the log message handler to the logger
            handler = logging.handlers.RotatingFileHandler(logfile,
                                                           maxBytes=2 * 1024 * 1024,
                                                           backupCount=5)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.info('Initialized and logging turned ON')
            self.logging = True
        except Exception as e:
            self.logging = False
            self.logger = None
            if self._debug:
                print('Probe ' + self.name + ' logging could not be initialized')
                print(e)
            raise CatascopiaProbeStatusException('Probe ' + self.name + ' logging could not be initialized'
                                                 + 'error reported ' + e)

    # TODO support configurable log level e.g. info, debug, critical...
    def _writeToLog(self, msg):
        if self.logging:
            self.logger.info(msg)

    def attachQueue(self, queue=None):
        # if no queue is provided then a new one is created and returned
        if queue is None:
            self.queue = Queue(maxsize = 1000000) # maxsize should not be hardcoded
        else:
            self.queue = queue
        self._writeToLog('Queue attached to Probe')
        return self.queue

    def dettachQueue(self):
        self.queue = None
        self._writeToLog('Queue detached from Probe')

    @abc.abstractmethod
    def get_desc(self):
        """method that returns Probe desc as provided by Probe Developer"""
        return "The Developer of this Probe didn't provide a description"

    def get_probeid(self):
        return self.probeid

    def set_probeid(self, probeid):
        # NOT in favor of keeping this method... danger hinders...
        self.probeid = probeid

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_periodicity(self):
        return self.periodicity

    def set_periodicity(self, periodicity):
        # periodicity set in seconds
        self.periodicity = periodicity

    def get_probestatus(self):
        """method that returns probe status... INACTIVE, ACTIVE, TERM
        """
        return self.probestatus

    def set_probestatus(self, status):
        if ProbeStatus.contains(status):
            self.probestatus = status
        else:
            raise CatascopiaProbeStatusException('Probe ' + self.name + ', attempted to set invalid probe status')

    def add_metric(self, metric):
        metric.set_group(self.name) # make this optional?
        self.metrics[metric.get_name()] = metric

    def get_metric(self, name):
        return self.metrics.get(name)

    def get_metrics(self):
        return self.metrics

    def get_metrics_as_list(self):
        return self.metrics.values()

    def get_debugmode(self):
        return self._debug

    def set_debugmode(self, debug):
        self._debug = True

    def activate(self):
        """method to ACTIVATE data collection"""
        if self.get_probestatus() == ProbeStatus.INACTIVE:
            # only want to start the thread once
            if self._first:
                self.start()
                self._first = False
            # thread you can now 'unpause'
            self._activateEvent.set()
            self.probestatus = ProbeStatus.ACTIVE
            if self._debug:
                print('Probe ' + self.name + ' Data collection ACTIVATED')
            self._writeToLog('Data collection ACTIVATED')

    def deactivate(self):
        """method to DEACTIVATE data collection"""
        # if probe is already INACTIVE, no need to do anything
        if self.get_probestatus() == ProbeStatus.ACTIVE:
            # thread you are now 'magically' paused
            self._activateEvent.clear()
            self.probestatus = ProbeStatus.INACTIVE
            if self._debug:
                print('Probe ' + self.name + ' Data collection DEACTIVATED')
            self._writeToLog('Data collection DEACTIVATED')

    def terminate(self):
        """method to TERM Probe"""
        if not self._activateEvent.isSet():
            self._activateEvent.set()
        self.probestatus = ProbeStatus.TERM
        if self._debug:
            print('Probe ' + self.name + ' Data collection TERMINATED')
        self._writeToLog('Data collection TERMINATED')

    def run(self):
        """method that overrides thread run()
           Invokes Probe Developers collect() method to collect metrics
        """
        # loop until Probe termination is requested
        while (self.probestatus != ProbeStatus.TERM):
            # if probe ACTIVE collect data
            if self.probestatus == ProbeStatus.ACTIVE and self._activateEvent.isSet():
                try:
                    self.collect()
                    for m in self.metrics.values():
                        # if probe has queue attached then push for consumption
                        if self.queue:
                            self.queue.put(str(m), timeout = 1) #timeout should not be hardcoded
                        if self._debug:
                            print(m)
                except (TypeError, AttributeError) as e:
                    s = 'CRITICAL data collection FAILED with error: ' + str(e)
                    if self._debug:
                        print('Probe ' + self.name + ', ' + s)
                    self._writeToLog(s)
                    self.errors += 1
                    if self.errors > Probe.__MAX_PERMITTED_ERRORS:
                        self._writeToLog('TERMINATTING due to too many ERRORS')
                        self.terminate()
                    else:
                        time.sleep(self.period * self.errors)
                self.errors = 0
                time.sleep(self.periodicity)
            else:
                # if INACTIVE wait until activated
                self._activateEvent.wait()
        # clean up before termination
        self.cleanUp()

    @abc.abstractmethod
    def collect(self):
        """Probe Developer must override this method to collect values"""
        pass


    def cleanUp(self):
        """Probe Developer can override this method to clean up before TERM"""
        pass


class ProbeStatus:
    typeNum = 3
    INACTIVE, ACTIVE, TERM = range(3)
    _typeStrings = { 0 : 'INACTIVE',
                     1 : 'ACTIVE',
                     2: 'TERM'
                    }

    @staticmethod
    def __contains__(t):
        return False if (t not in range(ProbeStatus.typeNum)) else True

    @staticmethod
    def type_as_string(t):
        return ProbeStatus._typeStrings.get(t)


class CatascopiaProbeStatusException(Exception):
    pass



