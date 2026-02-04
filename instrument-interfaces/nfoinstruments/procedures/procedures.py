#TODO: Implement logging, metadata

from time import sleep
from pymeasure.experiment import Procedure, IntegerParameter

# New import paths
from nfoinstruments.drivers.setup import DummyResource

from .lcr import *
from .impedance_analyzer import *


class DummyProcedure(Procedure):

    

    # a list defining the order and appearance of columns in our data file
    DATA_COLUMNS = ['Number', 'Time_since_init', 'Time_since_start']

    def __init__(self, setup):

        # a Parameter that defines the number of loop iterations
        self.number_of_measurements = IntegerParameter('Number of measurements')
        
        
        self._setup = setup
        self._setup.connect_to_devices({1: DummyResource})
        self._init_time = self._setup.devices[1].read()
        super().__init__()

    def execute(self):
        """Execute the procedure.

        Loops over each iteration and emits the current time,
        before waiting for 0.01 sec, and then checking if the procedure
        should stop.
        """
        self._start_time = self._setup.devices[1].read()
        for i in range(self.number_of_measurements):
            data = self._setup.devices[1].read()
            self.emit('results', {
                'Number': i,
                'Time_since_init': data - self._init_time,
                'Time_since_start': data - self._start_time,
                })
            sleep(0.01)
            if self.should_stop():
                break