"""
nfoinstruments.procedures - Measurement Procedure Module

PyMeasure-based measurement procedures for automated data collection.

Modules:
    - measurement: Measurement class for running procedures
    - lcr: LCR-based impedance spectroscopy procedures
    - impedance_analyzer: HP4291A impedance analyzer procedures
    - utils: Helper functions for measurements
"""

from .measurement import Measurement
from .lcr import ISProcedurePPMS, ISProcedureConstTemp
from .impedance_analyzer import IAProcedure
from .procedures import DummyProcedure
from .utils import (
    set_temperature_and_wait, 
    set_bias_and_wait,
    sweep_frequency_lcr,
    load_measurement_files,
    plot_all_measurements,
    plot_measurement_comparison
)

__all__ = [
    'Measurement',
    'ISProcedurePPMS',
    'ISProcedureConstTemp',
    'IAProcedure',
    'DummyProcedure',
    'set_temperature_and_wait',
    'set_bias_and_wait',
    'sweep_frequency_lcr',
    'load_measurement_files',
    'plot_all_measurements',
    'plot_measurement_comparison',
]
