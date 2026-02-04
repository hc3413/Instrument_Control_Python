# Instrument Control Python

Python code to control laboratory instruments for automated measurements. Supports temperature controllers (Janis, PPMS) and LCR meters (Agilent E4980A) for impedance spectroscopy experiments.

## Platform Compatibility

This project is designed to work on both **macOS** (for development) and **Windows** (for actual instrument control). All code uses `pathlib` and cross-platform libraries to ensure compatibility.

## Project Structure

```
Instrument_Control_Python/
├── instrument-interfaces/       # Core instrument control package
│   ├── nfoinstruments/
│   │   ├── drivers/            # Instrument driver classes
│   │   │   ├── lcr.py         # E4980A LCR meter, HP4291A analyzer
│   │   │   ├── temperature.py # Janis and PPMS controllers
│   │   │   └── setup.py       # MeasurementSetup class
│   │   ├── procedures/         # Measurement procedures
│   │   │   ├── utils.py       # Helper functions for measurements
│   │   │   ├── lcr.py         # LCR-specific procedures
│   │   │   └── measurement.py # PyMeasure integration
│   │   └── docs/              # Package documentation
│   └── setup.py               # Package installation
│
├── Jupyter Scripts/            # Example scripts and notebooks
│   ├── example_1_single_temp.py      # Single temperature measurement
│   ├── example_2_temp_sweep.py       # Temperature series
│   ├── example_3_temp_bias_sweep.py  # Temperature + bias sweep
│   └── Agilent_Janis_Control.ipynb   # Interactive notebook
│
└── README.md                   # This file
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/hc3413/Instrument_Control_Python.git
cd Instrument_Control_Python
```

### 2. Install the package

On both macOS and Windows:

```bash
cd instrument-interfaces
pip install -e .
```

This installs the `nfoinstruments` package in editable mode, so changes are immediately available.

### 3. Install dependencies

The package requires:
- `pyvisa` - VISA instrument communication
- `pymeasure` - Experiment framework (optional, for structured procedures)
- `numpy` - Numerical operations

These will be installed automatically via `setup.py`.

## Quick Start

### Basic Usage - Single Temperature Measurement

```python
from nfoinstruments.drivers import Janis, E4890A
from nfoinstruments.drivers.setup import MeasurementSetup
from nfoinstruments.procedures import set_temperature_and_wait, sweep_frequency_lcr
import numpy as np

# Connect to instruments
mm = MeasurementSetup()
mm.connect_to_devices({
    'GPIB0::16::INSTR': Janis,
    'GPIB0::17::INSTR': E4890A
})

janis = mm.devices['GPIB0::16::INSTR']
lcr = mm.devices['GPIB0::17::INSTR']

# Configure LCR meter
lcr.measurement_type = E4890A.MeasurementType.ZTD  # Impedance magnitude & phase
lcr.signal_amplitude = 0.05  # 50 mV
lcr.bias = 0.0

# Set temperature and measure
target_temp = 300  # Kelvin
actual_temp = set_temperature_and_wait(janis, target_temp, extra_settle_time=30, verbose=True)

# Frequency sweep
frequency_points = np.logspace(np.log10(20), np.log10(2e6), 100)  # 20 Hz to 2 MHz
with open("measurement_data.csv", "w") as f:
    f.write("# time,bias,frequency,NA,Z,theta\n")
    sweep_frequency_lcr(janis, lcr, frequency_points, f, verbose=True)
```

See the `Jupyter Scripts/` folder for complete examples.

## Key Features

### 🎯 Clear Instrument Classes

Each instrument has a dedicated driver class with well-defined properties:

**LCR Meter (E4980A)**
- `frequency` - Measurement frequency (20 Hz - 2 MHz)
- `signal_amplitude` - AC signal amplitude
- `bias` - DC bias voltage
- `measurement_type` - Using Enums (e.g., `E4890A.MeasurementType.ZTD`)
- `measurement` - Returns [Z, theta] or [R, X] depending on mode

**Temperature Controller (Janis)**
- `temperature` - Current temperature (read-only)
- `temperature_setpoint` - Target temperature (read/write)
- `temperature_stable` - Boolean indicating stability
- `max_heater_power` - Maximum heater power (%)

### Composable Measurement Functions

Simple utility functions that you can combine for complex measurements:

```python
# Temperature control
actual_temp = set_temperature_and_wait(janis, 300, extra_settle_time=30)

# Frequency sweep
sweep_frequency_lcr(janis, lcr, frequencies, output_file)

# Bias control
set_bias_and_wait(lcr, 1.0, settle_time=0.5)
```

### Stacked Measurements

Create complex measurement sequences by stacking simple operations:

```python
# Temperature sweep with frequency sweeps at each temperature
for temp in [300, 280, 260, 240, 220, 200]:
    actual_temp = set_temperature_and_wait(janis, temp, extra_settle_time=30)
    
    with open(f"data_T{actual_temp:.0f}.csv", "w") as f:
        f.write("# time,bias,frequency,NA,Z,theta\n")
        sweep_frequency_lcr(janis, lcr, frequency_points, f, verbose=True)
```

## Examples

Three example scripts are provided in `Jupyter Scripts/`:

1. **example_1_single_temp.py** - Basic impedance spectroscopy at one temperature
2. **example_2_temp_sweep.py** - Impedance spectroscopy at multiple temperatures
3. **example_3_temp_bias_sweep.py** - Temperature sweep with bias sweeps at each temperature

## Syncing Between Mac and Windows

This repository is set up to sync between your Mac (for development) and Windows machine (for measurements):

1. **On Mac**: Edit code, commit and push to GitHub
2. **On Windows**: Pull latest changes before running measurements

```bash
# On Windows machine
cd C:\path\to\Instrument_Control_Python
git pull origin main
```

## Documentation

- See `instrument-interfaces/docs/QUICKSTART.md` for detailed setup
- See `instrument-interfaces/docs/INSTRUMENTS.md` for instrument API reference
- See `instrument-interfaces/README.md` for package-specific documentation

## Supported Instruments

### LCR Meters
- Agilent E4980A (20 Hz - 2 MHz)
- HP/Agilent 4291A RF Impedance Analyzer (1 MHz - 1.8 GHz)

### Temperature Controllers
- Janis Probe Station
- PPMS (Physical Property Measurement System)

## Contributing

When adding new instruments:
1. Create driver class in `instrument-interfaces/nfoinstruments/drivers/`
2. Use abstract base classes (ABC) for consistency
3. Add helper functions in `procedures/utils.py` if needed
4. Create example scripts demonstrating usage
5. Ensure Windows compatibility (use `pathlib`, avoid Unix-specific commands)

## License

MIT License - See LICENSE file for details
