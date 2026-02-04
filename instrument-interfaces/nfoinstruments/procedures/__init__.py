"""
nfoinstruments.procedures - Measurement Procedure Module

PyMeasure-based measurement procedures for automated data collection.

Modules:
    - measurement: Measurement class for running procedures
    - lcr: LCR-based impedance spectroscopy procedures
    - impedance_analyzer: HP4291A impedance analyzer procedures
    - utils: Helper functions for measurements
"""

# Try to import Measurement class, but make it optional if tkinter is not available
try:
    from .measurement import Measurement
except (ImportError, ModuleNotFoundError):
    Measurement = None
    import warnings
    warnings.warn(
        "Measurement class not available (tkinter not installed). "
        "This is okay if you're only using the utility functions.",
        ImportWarning
    )

from .lcr import ISProcedurePPMS, ISProcedureConstTemp
from .impedance_analyzer import IAProcedure
from .procedures import DummyProcedure
from .utils import (
    set_temperature_and_wait, 
    set_bias_and_wait,
    sweep_frequency_lcr,
    single_frequency_time_scan,
    load_measurement_files,
    plot_all_measurements,
    plot_measurement_comparison,
    plot_time_scan_comparison
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
    'single_frequency_time_scan',
    'load_measurement_files',
    'plot_all_measurements',
    'plot_measurement_comparison',
    'plot_time_scan_comparison',
]
