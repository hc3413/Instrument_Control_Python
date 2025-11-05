"""
nfoinstruments - Instrument Control Package

This package provides drivers and procedures for controlling scientific instruments
via GPIB/VISA, focusing on LCR meters, impedance analyzers, temperature controllers, 
and automated measurement procedures.

Subpackages:
    - drivers: Low-level instrument drivers (LCR/impedance, temperature stages)
    - procedures: Measurement procedures using PyMeasure framework
    - utils: Utility functions and helpers

Supported Instruments:
    - E4890A: Agilent LCR Meter (20 Hz - 2 MHz)
    - HP4291A: HP/Agilent RF Impedance Analyzer (1 MHz - 1.8 GHz)
    - PPMS: Physical Property Measurement System
    - Janis: Janis Probe Station Temperature Controller

Authors: Ewout van der Veer, Horatio Cox
"""

__version__ = '0.2.0'

# Import main classes for convenient access
from nfoinstruments.drivers.setup import MeasurementSetup, InstrumentError
from nfoinstruments.drivers.lcr import E4890A, HP4291A
from nfoinstruments.drivers.temperature import PPMS, Janis

__all__ = [
    'MeasurementSetup',
    'InstrumentError',
    'E4890A',
    'HP4291A',
    'PPMS',
    'Janis',
]