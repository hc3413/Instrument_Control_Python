# nfoinstruments - Instrument Control Package

Python package for controlling scientific instruments via GPIB/VISA, with focus on LCR meters, temperature controllers, and automated measurement procedures.

## Features

- **Type-safe instrument control** using Python Enums
- **Multiple instrument support**: Agilent E4890A LCR meter, PPMS, Janis temperature controllers
- **PyMeasure integration** for structured experiment workflows
- **Automated measurement procedures** for impedance spectroscopy, temperature sweeps, etc.
- **Clean architecture** separating drivers from measurement logic

## Installation

```bash
cd C:\Users\F110216\Documents\Instrument_Control_Python\instrument-interfaces
pip install -e .
```

## Quick Start

```python
from nfoinstruments import MeasurementSetup, E4890A, Janis
import numpy as np
from time import sleep

# Connect to instruments
mm = MeasurementSetup()
mm.connect_to_devices({
    'GPIB0::16::INSTR': Janis,
    'GPIB0::17::INSTR': E4890A
})
janis = mm.devices['GPIB0::16::INSTR']
lcr = mm.devices['GPIB0::17::INSTR']

# Configure LCR meter (note: use Enums!)
lcr.measurement_time = E4890A.MeasurementTime.MEDIUM
lcr.measurement_type = E4890A.MeasurementType.ZTD
lcr.signal_amplitude = 0.05
lcr.averages = 5

# Set temperature and measure
janis.temperature_setpoint = 300
while not janis.temperature_stable:
    sleep(10)

# Frequency sweep
frequencies = np.logspace(1, 6, 50)
for freq in frequencies:
    lcr.frequency = freq
    result = lcr.measurement  # Returns [Z, theta]
    print(f"{freq} Hz: Z={result[0]:.2e} Ω, θ={result[1]:.2f}°")
```

## Package Structure

```
nfoinstruments/
├── drivers/              # Instrument drivers
│   ├── setup.py         # MeasurementSetup (resource manager)
│   ├── lcr.py           # LCR meters & impedance analyzers (E4890A, HP4291A)
│   └── temperature.py   # Temperature controllers (PPMS, Janis)
│
├── procedures/          # PyMeasure measurement procedures
│   ├── measurement.py   # Measurement runner class
│   ├── lcr.py          # Impedance spectroscopy procedures
│   └── utils.py        # Helper functions
│
└── docs/               # Documentation
    ├── QUICKSTART.md
    ├── INSTRUMENTS.md
    └── PROCEDURES.md
```

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get up and running fast
- **[Instrument Documentation](docs/INSTRUMENTS.md)** - Detailed instrument APIs
- **[Code Structure Guide](../CODE_STRUCTURE_GUIDE.md)** - Architecture overview
- **[Consolidation Plan](../CONSOLIDATION_PLAN.md)** - Migration details

## Supported Instruments

### LCR Meters & Impedance Analyzers
- Agilent E4890A LCR Meter (20 Hz - 2 MHz)
- HP/Agilent 4291A RF Impedance Analyzer (1 MHz - 1.8 GHz)

### Temperature Controllers
- Physical Property Measurement System (PPMS)
- Janis Probe Station

## Key Concepts

### Enums for Type Safety

Always use Enums instead of strings for instrument parameters:

```python
# ❌ Don't do this
lcr.measurement_time = 'MEDIUM'

# ✅ Do this instead
lcr.measurement_time = E4890A.MeasurementTime.MEDIUM
```

### Available Enums

**E4890A.MeasurementTime:** `SHORT`, `MEDIUM`, `LONG`  
**E4890A.SignalType:** `VOLTAGE`, `CURRENT`  
**E4890A.MeasurementType:** `ZTD`, `ZTR`, `CPD`, `CSD`, `RX`, and many more

See [INSTRUMENTS.md](docs/INSTRUMENTS.md) for complete list.

## Examples

See the `examples/` directory for complete Jupyter notebooks:
- Basic LCR measurements
- Temperature sweeps with Janis
- Multi-parameter measurements
- Data analysis examples

## Import Styles

You can import classes in two ways:

```python
# Simple (recommended) - after pip install -e .
from nfoinstruments import MeasurementSetup, E4890A, Janis

# Explicit module imports
from nfoinstruments.drivers.setup import MeasurementSetup
from nfoinstruments.drivers.lcr import E4890A
from nfoinstruments.drivers.temperature import Janis
```

## Requirements

- Python 3.7+
- PyVISA
- PyMeasure
- NumPy
- NI-VISA or similar VISA backend

## Development

```bash
# Install in development mode
pip install -e .

# Run tests (when available)
pytest tests/
```

## Version History

- **0.2.0** - Major restructure: `drivers/` and `procedures/` architecture, Enum support, removed legacy code
- **0.1.0** - Initial implementation

## Contributing

When adding new instruments:
1. Create driver class in `drivers/`
2. Inherit from appropriate base class (LCR, TemperatureStage)
3. Use Enums for all configuration parameters
4. Add documentation to `docs/INSTRUMENTS.md`
5. Create example notebook

## License

[Add your license here]

## Authors

- Ewout van der Veer
- Horatio Cox

## Support

For issues or questions:
- Check documentation in `docs/`
- Review examples in `examples/`
- See troubleshooting in [QUICKSTART.md](docs/QUICKSTART.md)
