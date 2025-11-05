from pprint import pprint
from time import sleep
from collections import namedtuple
from abc import ABC, abstractmethod

from .setup import InstrumentError

class TemperatureStage(ABC):
    
    @property
    @abstractmethod
    def temperature(self):
        pass

    @property
    @abstractmethod
    def temperature_stable(self):
        pass

    @property
    @abstractmethod
    def temperature_setpoint(self):
        pass

    @temperature_setpoint.setter
    @abstractmethod
    def temperature_setpoint(self, setpoint):
        pass

class PPMS(TemperatureStage):
    """Class representing a Physical Property Measurement System (PPMS)."""

    PPMSstatus = namedtuple('PPMSstatus', ['temperature', 'field', 'chamber', 'position'])

    def __init__(self, address, resman):
        """
        Initialize the PPMS object.

        Args:
            address (str): Address of the PPMS instrument.
            resman: PyVISA resource manager instance.
        """

        self.address = address
        self.resource = resman.open_resource(self.address, read_termination=';', write_termination=';', query_delay=0.1)

        self._temperature = None
        self._temperature_setpoint = None
        self._temperature_rate = None
        self._temperature_approach_mode = None

        self._field = None
        self._field_setpoint = None
        self._field_rate = None
        self._field_approach_mode = None
        self._magnet_mode = None

        self._position = None
        self._helium_level = None
        self._status = None

        self.print_status()

    def print_status(self):
        """
        Print the current status of the PPMS.
        """

        self._update_status()
        pprint(vars(self))
        
    def _update_status(self):
        for i in range(5):
            try:
                self.resource.clear()
                data = self.resource.query('GETDAT? 15').split(',')
                _, _, status, temp, field, pos = data
                self._temperature = float(temp)
                self._field = float(field)
                self._position = float(pos)
                stat_bin = int(status)
                self._status = self.PPMSstatus(temperature=int(stat_bin & 15),
                                               field=round(int(stat_bin & 240)/2**4),
                                               chamber=round(int(stat_bin & 3840)/2**8),
                                               position=round(int(stat_bin & 61440)/2**12)) #Magic
                
                temp_setpt, temp_rate, temp_appr_mode = self.resource.query('TEMP?').split(',')
                self._temperature_setpoint = float(temp_setpt)
                self._temperature_rate = float(temp_rate)
                self._temperature_approach_mode = float(temp_appr_mode)

                field_setpt, field_rate, field_appr_mode, magnet_mode = self.resource.query('FIELD?').split(',')
                self._field_setpoint = float(field_setpt)
                self._field_rate = float(field_rate)
                self._field_approach_mode = float(field_appr_mode)
                self._magnet_mode = float(magnet_mode)

                helium_lev = self.resource.query('LEVEL?').split(',')[0]
                self._helium_level = float(helium_lev)
            except:
                sleep(1)
                continue
            else:
                return
        raise IOError("Could not determine PPMS state.")

    @property
    def temperature(self):
        """
        Get the current temperature of the PPMS.

        Returns:
            float: The current temperature.
        """

        self._update_status()
        return self._temperature

    @property
    def temperature_stable(self):
        """
        This function determines whether the current temperature has stabilized at the setpoint.
        """

        self._update_status()
        if self._status[3] in (5, 6, 7) or \
            abs(self._temperature - self._temperature_setpoint) > 0.2: 
            return False
        if self._status[3] in (1, 2):
            return True
        raise IOError("Error in PPMS temperature control.")
    
    @property
    def field_stable(self):
        """This function determines whether the current magnetic field has stabilized at the setpoint."""
        self._update_status()
        if self._status[2] in (2, 3, 5, 6, 7) or \
            abs(self._field - self._field_setpoint) > 2: 
            return False
        if self._status[2] in (1, 4):
            return True
        raise IOError("Error in PPMS field control.")
    
    @property
    def chamber(self):
        """This function returns the status of the sample chamber."""

        self._update_status()
        if self._status[1] in (1, 2, 4, 5, 8, 9): return self._status[1]
        raise IOError("Error in sample chamber status.")

    @chamber.setter
    def chamber(self, chamber_code):
        """Sets a new chamber code."""

        if chamber_code in (0,1,2,3,4):
            self.resource.write(f"CHAMBER {chamber_code}")
            return
        raise ValueError("Invalid chamber code.")
    
    def seal(self): self.chamber = 0
    def purge(self): self.chamber = 1
    def vent_seal(self):
        self._update_status()
        if self._temperature > 320 or self._temperature < 290:
            raise InstrumentError("temperature too high or too low to vent")
        self.chamber = 2
    def pump(self): self.chamber = 3
    def vent_continuous(self): 
        self._update_status()
        if self._temperature > 320 or self._temperature < 290:
            raise InstrumentError("temperature too high or too low to vent")
        self.chamber = 4
    def _force_vent_continuous(self): self.chamber = 4
    
    @property
    def sample_position(self):
        """This function returns the status of the sample chamber."""
        self._update_status()
        if self._status[0] in (1, 5, 8, 9): return self._status[0]
        raise IOError("Error in sample position status.")

    @property
    def temperature_setpoint(self):
        self._update_status()
        return (self._temperature_setpoint, 
                self._temperature_rate, 
                self._temperature_approach_mode)

    @temperature_setpoint.setter
    def temperature_setpoint(self, setpoint):
        if len(setpoint) != 3:
            raise ValueError("setpoint must have three components: value, rate, approach mode")
        if (type(setpoint[2]) == int or type(setpoint[2]) == float) and not setpoint[2] in [0, 1]:
            raise ValueError("approach mode must be 0/'fast settle' or 1/'no overshoot'")
        if (type(setpoint[2]) == str) and not setpoint[2] in ['fast settle', 'no overshoot']:
            raise ValueError("approach mode must be 0/'fast settle' or 1/'no overshoot'")
        if setpoint[2] in ['fast settle', 'no overshoot']:
            appr_mode_dict = {'fast settle': 0, 'no overshoot': 1}
            self.resource.write(f"TEMP {setpoint[0]} {setpoint[1]} {appr_mode_dict[setpoint[2]]}")
            return
        self.resource.write(f"TEMP {setpoint[0]} {setpoint[1]} {setpoint[2]}")

    @property
    def field_setpoint(self):
        self._update_status()
        return (self._field_setpoint, 
                self._field_rate, 
                self._field_approach_mode)

    @field_setpoint.setter
    def field_setpoint(self, setpoint):
        if len(setpoint) != 4:
            raise ValueError("setpoint must have four components: value, rate, approach mode, magnet mode")
        self.resource.write(f"FIELD {setpoint[0]} {setpoint[1]} {setpoint[2]} {setpoint[3]}")

class Janis(TemperatureStage):
    """Class representing the Janis probe station temperature controller."""

    def __init__(self, address, resman):
        """
        Initialize the Janis object.

        Args:
            address (str): Address of the Janis instrument.
            resman: PyVISA resource manager instance.
        """

        self.address = address
        self.resource = resman.open_resource(self.address, query_delay=0.1)

        self._temperature = None
        self._temperature_setpoint = None
        self._temperature_rate = None
        self._temperature_approach_mode = None
        self._mhp = 75.0
        self._temp_stable_time = 1
        
        self.initialize()

    def initialize(self):
        self.resource.write(f"SET {self.temperature}") 
        self.resource.write(f"MHP {self._mhp}")
        self.resource.write('MODE 2')
        self.resource.write('CTYP 1')

    @property
    def temperature(self):
        """
        Get the current temperature of the Janis controller.

        Returns:
            float: The current temperature.
        """
        self._temperature = float(self.resource.query("TA?")[3:-2])
        return self._temperature
    
    @property
    def max_heater_power(self):
        return self._mhp
    
    @max_heater_power.setter
    def max_heater_power(self, setpoint):
        setpoint = round(float(setpoint))
        if setpoint < 0.0 or setpoint > 100.0:
            print("Max. heater power must be between 0 and 100 %")
            return
        if setpoint > 75.0:
            print("WARNING: Setting max. heater power higher than 75 % may lead to errors")
        self._mhp = setpoint
        self.resource.write(f"MHP {self._mhp}")

    @property
    def temperature_stable(self):
        """
        This function determines whether the current temperature has stabilized at the setpoint.
        """
        temps = [self._temperature_setpoint]
        for _ in range(3):
            temps.append(self.temperature)
            sleep(self._temp_stable_time)
        return max(temps)-min(temps) < 0.1

    @property
    def temperature_setpoint(self):
        return self._temperature_setpoint

    @temperature_setpoint.setter
    def temperature_setpoint(self, setpoint):
        try:
            self._temperature_setpoint = float(setpoint)
            self.resource.write(f"SET {self._temperature_setpoint}")
        except:
            print("invalid temperature setpoint")
