from time import sleep, time
from pymeasure.experiment import Procedure,\
                                 IntegerParameter,\
                                 FloatParameter,\
                                 ListParameter,\
                                 BooleanParameter

# Import from consolidated lcr module
from nfoinstruments.drivers.lcr import HP4291A

class IAProcedure(Procedure):
    """
    Procedure for doing impedance spectroscopy at different temperatures
    and bias offsets using the HP 4291A impedance analyzer. 
    """

    # a list defining the order and appearance of columns in our data file
    DATA_COLUMNS = ['Frequency','Bias', 'R', 'X', 'Rraw', 'Xraw']

    def __init__(self, setup, ia_addr):

        self._setup = setup
        self._setup.connect_to_devices({
                                        ia_addr: HP4291A
                                        })

        self._ia = self._setup.devices[ia_addr]

        super().__init__()

    def execute(self):
        for _ in range(10):
            self._emit_measurement_data()

    def _emit_measurement_data(self):
        res = self._ia.measure()
        print(res)
        self.emit('results', {
                'Frequency': 0,
                'Bias': 0,
                'R': 0,
                'X': 0,
                'Rraw': 0,
                'Xraw': 0,
            })