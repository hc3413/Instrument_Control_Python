# Quick Start Guide

## Installation

Navigate to the `instrument-interfaces` directory and install in development mode:

```bash
cd C:\Users\F110216\Documents\Instrument_Control_Python\instrument-interfaces
pip install -e .
```

This makes the package importable from anywhere on your system.

## Basic Usage

### 1. Import the Package

**Recommended (simple):**
```python
from nfoinstruments import MeasurementSetup, E4890A, Janis, PPMS
```

**Also works (explicit imports):**
```python
from nfoinstruments.drivers.setup import MeasurementSetup
from nfoinstruments.drivers.lcr import E4890A
from nfoinstruments.drivers.temperature import Janis, PPMS
```

### 2. Connect to Instruments

```python
import numpy as np
from time import sleep

# Create measurement setup
mm = MeasurementSetup()

# Connect to instruments
mm.connect_to_devices({
    'GPIB0::16::INSTR': Janis,      # Temperature controller
    'GPIB0::17::INSTR': E4890A      # LCR meter
})

# Get device references
janis = mm.devices['GPIB0::16::INSTR']
lcr = mm.devices['GPIB0::17::INSTR']
```

### 3. Configure the LCR Meter

**Important: Always use Enums, never strings!**

```python
# Configure measurement parameters
lcr.measurement_time = E4890A.MeasurementTime.MEDIUM
lcr.measurement_type = E4890A.MeasurementType.ZTD  # Impedance magnitude & phase
lcr.signal_type = E4890A.SignalType.VOLTAGE
lcr.signal_amplitude = 0.05  # 50 mV
lcr.averages = 5
lcr.bias = 0
lcr.alc_enabled = True
```

### 4. Control Temperature

**Janis (simple):**
```python
janis.temperature_setpoint = 300  # Kelvin
while not janis.temperature_stable:
    print(f"Current: {janis.temperature:.1f} K")
    sleep(10)
```

**PPMS (more control):**
```python
# (temperature, rate K/min, approach mode)
ppms.temperature_setpoint = (300, 10, 'fast settle')
while not ppms.temperature_stable:
    sleep(5)
```

### 5. Take Measurements

**Single measurement:**
```python
lcr.frequency = 1000  # Hz
result = lcr.measurement  # Returns [primary, secondary]
print(f"Z = {result[0]:.2f} Ω, θ = {result[1]:.2f}°")
```

**Frequency sweep:**
```python
frequencies = np.logspace(np.log10(20), np.log10(2e6), 50)

with open("data.csv", "w") as f:
    f.write("frequency,Z,theta\\n")
    for freq in frequencies:
        lcr.frequency = freq
        sleep(0.1)
        result = lcr.measurement
        f.write(f"{freq},{result[0]},{result[1]}\\n")
```

## Complete Example

```python
from nfoinstruments import MeasurementSetup, E4890A, Janis
import numpy as np
from time import sleep

# Setup
mm = MeasurementSetup()
mm.connect_to_devices({
    'GPIB0::16::INSTR': Janis,
    'GPIB0::17::INSTR': E4890A
})
janis = mm.devices['GPIB0::16::INSTR']
lcr = mm.devices['GPIB0::17::INSTR']

# Configure LCR
lcr.measurement_time = E4890A.MeasurementTime.MEDIUM
lcr.measurement_type = E4890A.MeasurementType.ZTD
lcr.signal_amplitude = 0.05
lcr.averages = 5

# Define sweep
temperatures = [300, 250, 200]
frequencies = np.logspace(1, 6, 50)

# Measure
count = 1
for temp in temperatures:
    janis.temperature_setpoint = temp
    while not janis.temperature_stable:
        sleep(10)
    
    filename = f"run{count:03d}_T{temp}.csv"
    with open(filename, "w") as f:
        f.write("freq,Z,theta\\n")
        for freq in frequencies:
            lcr.frequency = freq
            sleep(0.1)
            result = lcr.measurement
            f.write(f"{freq},{result[0]},{result[1]}\\n")
    count += 1
```

## Common Issues

### "ValueError: measurement time must be SHORT, MEDIUM or LONG"
You're using strings instead of Enums. Fix:
```python
# ❌ Wrong
lcr.measurement_time = 'MEDIUM'

# ✅ Correct
lcr.measurement_time = E4890A.MeasurementTime.MEDIUM
```

### "ModuleNotFoundError: No module named 'nfoinstruments'"
Install the package:
```bash
cd C:\Users\F110216\Documents\Instrument_Control_Python\instrument-interfaces
pip install -e .
```

### GPIB Connection Errors
Check available devices:
```python
mm = MeasurementSetup()
print(mm.resources)  # Shows all detected GPIB addresses
```

## Next Steps

- See `INSTRUMENTS.md` for detailed instrument documentation
- See `PROCEDURES.md` for PyMeasure procedure examples
- Check `examples/` folder for complete notebooks
- Read `CODE_STRUCTURE_GUIDE.md` for architecture details
