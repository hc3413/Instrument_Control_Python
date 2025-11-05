import pyvisa
from time import time

class MeasurementSetup:
    """Class representing a measurement setup."""

    def __init__(self, debug=False):
        """Initialize the MeasurementSetup object."""

        self.resources = []

        if debug:
            self._resman = DummyResourceManager()
            return
        
        self._resman = pyvisa.ResourceManager()
        self._get_resources()

        if len(self.resources) == 0:
            raise InstrumentError("no devices found") 

        print(self.resources)

    def _get_resources(self):
        addresses = self._resman.list_resources()
        for addr in addresses:
            try:
                #Try to open the resource, them immediately close it again
                self._resman.open_resource(addr).close()
                self.resources.append(addr)
            except pyvisa.errors.VisaIOError:
                continue
        
    def connect_to_devices(self, addresses):
        self.devices = {}
        for addr, devcls in addresses.items():
            try:
                self.devices[addr] = devcls(addr, self._resman)
            except Exception as e:
                print(f"Could not connect to device {devcls} at address {addr}")
                print(e)

class InstrumentError(Exception):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"InstrumentError: {super().__str__()}"
    
class DummyResourceManager():
    """Class pretending to be a pyVISA ResourceManager for debugging purposes."""

    def __init__(self, **kwargs):
        pass

    def list_resources(self, **kwargs):
        return []
    
    def open_resource(self, addr, **kwargs):
        pass
    
class DummyResource():
    """Class pretending to be a pyVISA Resource for debugging purposes."""

    def __init__(self, address, resman, **kwargs):
        self._resman = resman
    
    def read(self, **kwargs):
        return time()