from time import sleep, time
from pymeasure.experiment import Procedure,\
                                 IntegerParameter,\
                                 FloatParameter,\
                                 ListParameter,\
                                 BooleanParameter

from nfoinstruments.drivers.temperature import PPMS
from nfoinstruments.drivers.lcr import E4890A

class ISProcedurePPMS(Procedure):
    """
    Procedure for doing impedance spectroscopy at different temperatures
    and bias offsets using the PPMS as the temperature controller. 
    """

    # a list defining the order and appearance of columns in our data file
    DATA_COLUMNS = ['Time', 'Bias', 'Frequency', 'Temperature', 'R', 'X']

    def __init__(self, setup, ppms_addr, lcr_addr):

        self._bias_points = ListParameter('bias_points', units='V')
        self._temperature_points = ListParameter('temperature_points', units='K')
        self._start_temperature = FloatParameter('start_temperature', units='K')
        self._frequency_points = ListParameter('frequency_points', units='Hz')
        self._no_overshoot = BooleanParameter('approach_mode', default=True)
        self._temperature_rate = FloatParameter('temperature_rate', units='K/min')
        



        self._setup = setup
        self._setup.connect_to_devices({
                                        ppms_addr: PPMS,
                                        lcr_addr: E4890A
                                        })

        self._ppms = self._setup.devices[ppms_addr]
        self._lcr = self._setup.devices[lcr_addr]

        super().__init__()

    def execute(self):
        self._settle_at_start_temp()

        for T_point in self.temperature_points:
            self._ppms.temperature_setpoint = (T_point, self.temperature_rate, self.approach_mode)
            while True:
                sleep(5)
                if self._ppms.temperature_stable:
                    break
            self._scan_bias()
            if self.should_stop():
                    break

    def _scan_bias(self):
        for b_point in self.bias_points:
            self._lcr.bias = b_point
            sleep(0.1)
            self._scan_frequency() 

    def _scan_frequency(self):
        for frequency in self.frequency_points:
            self._lcr.frequency = frequency
            sleep(0.1)
            self._emit_measurement_data()
            if self.should_stop():
                break

    def _emit_measurement_data(self):
        cap_res = self._lcr.measurement
        self.emit('results', {
                'Time': time(),
                'Bias': self._lcr.bias,
                'Frequency': self._lcr.frequency,
                'Temperature': self._ppms.temperature,
                'R': cap_res[0],
                'X': cap_res[1],
            })
            
    def _settle_at_start_temp(self):
        """
        Settle at the starting temperature.
        """
        self._ppms.temperature_setpoint = (self._start_temperature, 20, 'fast settle')
        while True:
            sleep(5)
            if self._ppms.temperature_stable:
                break

    @property
    def bias_points(self):
        """
        Get the bias points.

        Returns:
            tuple: A tuple of biases representing the bias points.
        """

        return self._bias_points

    @bias_points.setter
    def bias_points(self, points):
        """
        Set the bias points.

        Args:
            points (iterable): An iterable (list, tuple) of biases representing the bias points.

        Raises:
            ValueError: If the points format is invalid or the values are out of range.
        """

        if not hasattr(points, "__iter__"):
            raise ValueError("bias points must be an iterable (list, tuple) of temperatures")
        points = tuple(points) # In case a generator is passed
        if any(i<0 or i>40 for i in points):
            raise ValueError("one or more of the bias points exceeds the minimum or maximum bias") 
        self._bias_points = points

    @property
    def temperature_points(self):
        """
        Get the temperature points.

        Returns:
            tuple: A tuple of tuples representing the temperature points.
        """

        return self._temperature_points

    @temperature_points.setter
    def temperature_points(self, points):
        """
        Set the temperature points.

        Args:
            points (tuple): A tuple of tuples representing the temperature points.

        Raises:
            ValueError: If the points format is invalid or the values are out of range.
        """

        if not hasattr(points, "__iter__"):
            raise ValueError("temperature points must be an iterable (list, tuple) of temperatures")
        points = tuple(points) # In case a generator is passed
        if any(i<2 or i>400 for i in points):
            raise ValueError("one or more of the temperature points exceeds the minimum or maximum bias") 
        self._temperature_points = points

    @property
    def frequency_points(self):
        """
        Get the frequency points.

        Returns:
            tuple: A tuple of biases representing the frequency points.
        """

        return self._frequency_points

    @frequency_points.setter
    def frequency_points(self, points):
        """
        Set the frequency points.

        Args:
            points (iterable): An iterable (list, tuple) of biases representing the frequency points.

        Raises:
            ValueError: If the points format is invalid or the values are out of range.
        """

        if not hasattr(points, "__iter__"):
            raise ValueError("frequency points must be an iterable (list, tuple) of temperatures")
        points = tuple(points) # In case a generator is passed
        if any(i<20 or i>2_000_000 for i in points):
            raise ValueError("one or more of the frequency points exceeds the minimum or maximum") 
        self._frequency_points = points

    @property
    def frequency_range(self):
        pass

    @frequency_range.setter
    def frequency_range(self, frequency_range, num_points=100, logspaced=True):
        pass

    @property
    def start_temperature(self):
        """
        Get the starting temperature of the measurement.
        
        Returns:
            float: The starting temperature
        """
        return self._start_temperature

    @start_temperature.setter
    def start_temperature(self, start_temperature):
        """
        Set the starting temperature of the measurement.

        Args:
            start_temperature: The starting temperature.

        Raises:
            ValueError: If the value is out of range.
        """
        
        if start_temperature<2 or start_temperature>400:
            raise  ValueError("starting temperature must be between 2 and 400K")
        self._start_temperature = start_temperature

    @property
    def approach_mode(self):
        if self._no_overshoot:
            return 'no overshoot'
        return 'fast settle'
    
    @approach_mode.setter
    def approach_mode(self, mode):
        if mode not in ['fast settle', 'no overshoot']:
            raise ValueError("approach mode must be either 'fast settle' or 'no overshoot'")
        if mode == 'no overshoot':
            self._no_overshoot = True
            return
        self._no_overshoot = False
    
    @property
    def temperature_rate(self):
        return self._temperature_rate

    @temperature_rate.setter
    def temperature_rate(self, temperature_rate):        
        if temperature_rate<=0 or temperature_rate>20:
            raise  ValueError("temperature rate must be between 0 and 20K/min")
        self._temperature_rate = temperature_rate

class ISProcedureConstTemp(Procedure):
    """
    Procedure for doing impedance spectroscopy at different temperatures
    and bias offsets using the PPMS as the temperature controller. 
    """

    # a list defining the order and appearance of columns in our data file
    DATA_COLUMNS = ['Time', 'Bias', 'Frequency', 'Temperature', 'R', 'X']

    def __init__(self, setup, lcr_addr):

        self._bias_points = ListParameter('bias_points', units='V')
        self._frequency_points = ListParameter('frequency_points', units='Hz')
        
        self._setup = setup
        self._setup.connect_to_devices({
                                        lcr_addr: E4890A
                                        })

        self._lcr = self._setup.devices[lcr_addr]

        super().__init__()

    def execute(self):
        self._scan_bias()

    def _scan_bias(self):
        for b_point in self.bias_points:
            self._lcr.bias = b_point
            sleep(0.1)
            self._scan_frequency() 

    def _scan_frequency(self):
        for frequency in self.frequency_points:
            self._lcr.frequency = frequency
            sleep(0.1)
            self._emit_measurement_data()
            if self.should_stop():
                break

    def _emit_measurement_data(self):
        cap_res = self._lcr.measurement
        self.emit('results', {
                'Time': time(),
                'Bias': self._lcr.bias,
                'Frequency': self._lcr.frequency,
                'R': cap_res[0],
                'X': cap_res[1],
            })
            

    @property
    def bias_points(self):
        """
        Get the bias points.

        Returns:
            tuple: A tuple of biases representing the bias points.
        """

        return self._bias_points

    @bias_points.setter
    def bias_points(self, points):
        """
        Set the bias points.

        Args:
            points (iterable): An iterable (list, tuple) of biases representing the bias points.

        Raises:
            ValueError: If the points format is invalid or the values are out of range.
        """

        if not hasattr(points, "__iter__"):
            raise ValueError("bias points must be an iterable (list, tuple) of temperatures")
        points = tuple(points) # In case a generator is passed
        if any(i<0 or i>40 for i in points):
            raise ValueError("one or more of the bias points exceeds the minimum or maximum bias") 
        self._bias_points = points

    @property
    def frequency_points(self):
        """
        Get the frequency points.

        Returns:
            tuple: A tuple of biases representing the frequency points.
        """

        return self._frequency_points

    @frequency_points.setter
    def frequency_points(self, points):
        """
        Set the frequency points.

        Args:
            points (iterable): An iterable (list, tuple) of biases representing the frequency points.

        Raises:
            ValueError: If the points format is invalid or the values are out of range.
        """

        if not hasattr(points, "__iter__"):
            raise ValueError("frequency points must be an iterable (list, tuple) of temperatures")
        points = tuple(points) # In case a generator is passed
        if any(i<20 or i>2_000_000 for i in points):
            raise ValueError("one or more of the frequency points exceeds the minimum or maximum") 
        self._frequency_points = points

    @property
    def frequency_range(self):
        pass

    @frequency_range.setter
    def frequency_range(self, frequency_range, num_points=100, logspaced=True):
        pass