from pprint import pprint
from enum import Enum, auto
from abc import ABC, abstractmethod
from time import sleep

class LCR(ABC):
    
    @abstractmethod
    def print_status(self):
        pass

    @property
    @abstractmethod
    def frequency(self):
        pass

    @frequency.setter
    @abstractmethod
    def frequency(self, frequency):
        pass

    @property
    @abstractmethod
    def signal_amplitude(self):
        pass

    @signal_amplitude.setter
    @abstractmethod
    def signal_amplitude(self, signal_amplitude):
        pass

    @property
    @abstractmethod
    def measurement(self):
        pass

class E4890A(LCR):

    INSTRUMENT_ID = 'Agilent Technologies,E4980A,.+'

    class SignalType(Enum):
        CURRENT = auto()
        VOLTAGE = auto()

    class MeasurementTime(Enum):
        SHORT = 'SHOR'
        MEDIUM = 'MED'
        LONG = 'LONG'

    class MeasurementType(Enum):
        CPD = 'CPD'
        CPQ = 'CPQ'
        CPG = 'CPG'
        CPRP = 'CPRP'
        CSD = 'CSD'
        CSQ = 'CSQ'
        CSRS = 'CSRS'
        LPD = 'LPD'
        LPQ = 'LPQ'
        LPG = 'LPG'
        LPRD = 'LPRD'
        LSD = 'LSD'
        LSQ = 'LSQ'
        LSRD = 'LSRD'
        LSRS = 'LSRS'
        RX = 'RX'
        ZTD = 'ZTD'
        ZTR = 'ZTR'
        GB = 'GB'
        YTD = 'YTD'
        YTR = 'YTR'
        VDID = 'VDID'

    DEFAULT_AVERAGES = 1
    DEFAULT_BIAS = 0
    DEFAULT_FREQUENCY = 100
    DEFAULT_SIGNAL_AMPLITUDE = 1
    DEFAULT_MEASUREMENT_TIMEOUT = 20  # Increased from 10 to 20 seconds
    DEFAULT_ALC_ENABLED = True
    DEFAULT_MEASURMENT_TYPE = MeasurementType.RX
    DEFAULT_SIGNAL_TYPE = SignalType.VOLTAGE
    DEFAULT_MEASURMENT_TIME = MeasurementTime.MEDIUM

    def __init__(self, address, resman):
        self.address = address
        self.resource = resman.open_resource(self.address, query_delay=0.1)

        self.reset()
        self.print_status()

    def reset(self, keep_settings=False):
        if not keep_settings:
            self._measurement_time = self.DEFAULT_MEASURMENT_TIME
            self._averages = self.DEFAULT_AVERAGES
            self._bias = self.DEFAULT_BIAS
            self._frequency = self.DEFAULT_FREQUENCY
            self._measurement_type = self.DEFAULT_MEASURMENT_TYPE
            self._signal_amplitude = self.DEFAULT_SIGNAL_AMPLITUDE
            self.measurement_timeout = self.DEFAULT_MEASUREMENT_TIMEOUT
            self._signal_type = self.DEFAULT_SIGNAL_TYPE
            self._alc_enabled = self.DEFAULT_ALC_ENABLED
        
        self._initialize()

    def reboot(self):
        self.resource.write("SYSTEM:RESTART")

    def _initialize(self):
        self.resource.clear()
        self.resource.write("*CLS")
        
        # Verify connection and clear any pending errors
        try:
            idn = self.resource.query("*IDN?")
            print(f"LCR Connected: {idn.strip()}")
        except Exception as e:
            print(f"Warning: Failed to query IDN during initialization: {e}")

        self.resource.write('*RST')
        sleep(1.0) # Wait for reset to complete
        
        self.resource.write(f"APER {self._measurement_time.value}, {self._averages}")
        self.resource.write("BIAS:STAT OFF")
        self.resource.write(f"BIAS:VOLT {self._bias}")
        
        self.resource.write(f"FREQ {self._frequency}")
        self.resource.write(f"VOLT {self._signal_amplitude}")
        self.resource.write(f"FUNC:IMP:TYPE {self._measurement_type.value}")
        
        # Force Internal Trigger to prevent hanging if left in Manual/Bus mode
        self.resource.write("TRIG:SOUR INT")
        self.resource.write("INIT:CONT ON")
        
        self.resource.write("AMPL:ALC ON")
        self.resource.write("FORMAT ASCII")

        #Disable all corrections
        self.resource.write("CORR:OPEN:STAT OFF")
        self.resource.write("CORR:SHORT:STAT OFF")
        self.resource.write("CORR:LOAD:STAT OFF")
        self.resource.write(f"CORR:LENG 0")
        
        self.resource.timeout = self.measurement_timeout * 1000 #sec -> millisec
        #self.resource.clear()
        
    def print_status(self):
        """
        Print the current status of the LCR meter.
        """
        
        pprint(vars(self))
    
    @property
    def measurement_time(self):
        return self._measurement_time
    @measurement_time.setter
    def measurement_time(self, time):
        if not isinstance(time, E4890A.MeasurementTime):
            raise ValueError("measurement time must be SHORT, MEDIUM or LONG")
        self._measurement_time = time
        self.resource.write(f"APER {self._measurement_time.value}, {self._averages}")
        self._update_timeout()
    
    @property
    def averages(self):
        return self._averages

    @averages.setter
    def averages(self, averages):
        if not 1 <= averages <= 256:
            raise ValueError("number of averages must be between 1 and 256")
        self._averages = averages
        self.resource.write(f"APER {self._measurement_time.value}, {self._averages}")
        self._update_timeout()
    
    def _update_timeout(self):
        """Automatically adjust timeout based on measurement time and averages."""
        # Base times: SHORT=0.02s, MEDIUM=0.2s, LONG=2s per measurement
        base_times = {
            E4890A.MeasurementTime.SHORT: 0.02,
            E4890A.MeasurementTime.MEDIUM: 0.2,
            E4890A.MeasurementTime.LONG: 2.0
        }
        base_time = base_times.get(self._measurement_time, 0.2)
        # Calculate timeout: (base_time * averages) + 2 second buffer, minimum 5 seconds
        timeout = max(5.0, (base_time * self._averages) + 2.0)
        self.resource.timeout = int(timeout * 1000)  # Convert to milliseconds

    @property
    def bias(self):
        return self._bias

    @bias.setter
    def bias(self, bias):
        if self.signal_type == E4890A.SignalType.VOLTAGE:
            if not -40 <= bias <= 40:
                raise ValueError("bias must be between -40 and 40 V")
            self._bias = bias
            if bias == 0:
                self.resource.write(f"BIAS:STAT OFF")
                self.resource.write(f"BIAS:VOLT {self._bias}")
            else:
                self.resource.write(f"BIAS:VOLT {self._bias}")
                self.resource.write(f"BIAS:STAT ON")
        else:
            if not -0.1 <= bias <= 0.1:
                raise ValueError("bias must be between -0.1 and 0.1 A")
            self._bias = bias
            if bias == 0:
                self.resource.write(f"BIAS:STAT OFF")
                self.resource.write(f"BIAS:CURR {self._bias}")
            else:
                self.resource.write(f"BIAS:CURR {self._bias}")
                self.resource.write(f"BIAS:STAT ON")

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, frequency):
        if not 20 <= frequency <= 2_000_000:
            raise ValueError("frequency must be between 20 Hz and 2 MHz")
        self._frequency = frequency
        self.resource.write(f"FREQ {self._frequency}")

    @property
    def measurement_type(self):
        return self._measurement_type

    @measurement_type.setter
    def measurement_type(self, measurement_type):
        if not isinstance(measurement_type, E4890A.MeasurementType):
            raise ValueError("measurement type invalid")
        self._measurement_type = measurement_type
        self.resource.write(f"FUNC:IMP:TYPE {self._measurement_type.value}")

    @property
    def signal_amplitude(self):
        return self._signal_amplitude

    @signal_amplitude.setter
    def signal_amplitude(self, signal_amplitude):
        if self.signal_type == E4890A.SignalType.VOLTAGE:
            if not 0 <= signal_amplitude <= 20:
                raise ValueError("voltage signal amplitude must be between 0 and 20 V")
            self._signal_amplitude = signal_amplitude
            self.resource.write(f"VOLT {self._signal_amplitude}")
        elif self.signal_type == E4890A.SignalType.CURRENT:
            if not 0 <= signal_amplitude <= 0.1:
                raise ValueError("current signal amplitude must be between 0 and 0.1 A")
            self._signal_amplitude = signal_amplitude
            self.resource.write(f"CURR {self._signal_amplitude}")

    @property
    def signal_type(self):
        return self._signal_type

    @signal_type.setter
    def signal_type(self, signal_type):
        if not isinstance(signal_type, E4890A.SignalType):
            raise ValueError("signal type must be 'voltage' or 'current")
        self._signal_type = signal_type
        self.resource.write(f"CURR 0")

    @property
    def alc_enabled(self):
        return self._alc_enabled

    @alc_enabled.setter
    def alc_enabled(self, alc_enabled):
        if alc_enabled:
            self.resource.write("AMPL:ALC ON")
        else:
            self.resource.write("AMPL:ALC OFF")

    @property
    def measurement(self):
        result = self.resource.query("FETCH?").split(',')[0:2]
        return [float(val) for val in result]


# =============================================================================
# Impedance Analyzers (also measure LCR)
# =============================================================================

class ImpedanceAnalyzer(ABC):
    """Base class for impedance analyzers."""
    
    @abstractmethod
    def measure(self):
        pass


class HP4291A(ImpedanceAnalyzer):
    """HP/Agilent 4291A RF Impedance Analyzer (1 MHz - 1.8 GHz)"""
    
    INSTRUMENT_ID = 'HEWLETT-PACKARD,4291A,JP3KA00634,REV3.03'

    DEFAULT_SWEEP_AVERAGE = 1
    DEFAULT_POINT_AVERAGE = 1

    def __init__(self, address, resman):
        self.address = address
        self.resource = resman.open_resource(self.address, query_delay=0.1)

    def _reset_trigger(self):
        self.resource.write("TRIG:SOUR INT")
        self.resource.write("INIT:CONT OFF")
        self.resource.write("ABOR")
        self.resource.write("*SRE 4")
        self.resource.write("*CLS")
    
    def trigger(self):
        self.resource.write("*CLS")
        self.resource.write("INIT")

    def measure(self):
        """Perform measurement and return data array."""
        import numpy as np
        self._reset_trigger()
        self.trigger()
        self.resource.wait_for_srq(None)  # Do not timeout
        self.resource.write("FORM:DATA REAL,64")
        res_raw = self.resource.query_binary_values("DATA? DATA", datatype='d', is_big_endian=True)
        res = np.array(res_raw).reshape(2, int(len(res_raw)/2), order="F")
        return res
