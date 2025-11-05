# Instrument Documentation

## LCR Meters & Impedance Analyzers

### Agilent E4890A LCR Meter

**Import:**
```python
from nfoinstruments.drivers.lcr import E4890A
# or
from nfoinstruments import E4890A
```

#### Available Enums

**Measurement Time:**
- `E4890A.MeasurementTime.SHORT` - Fast measurements, lower accuracy
- `E4890A.MeasurementTime.MEDIUM` - Balanced speed/accuracy (recommended)
- `E4890A.MeasurementTime.LONG` - Slow measurements, highest accuracy

**Signal Type:**
- `E4890A.SignalType.VOLTAGE` - Voltage signal (most common)
- `E4890A.SignalType.CURRENT` - Current signal

**Measurement Type:**
- `E4890A.MeasurementType.ZTD` - Impedance magnitude (|Z|) and phase (θ)
- `E4890A.MeasurementType.ZTR` - Impedance real (R) and imaginary (X)
- `E4890A.MeasurementType.CPD` - Capacitance parallel (Cp) and dissipation (D)
- `E4890A.MeasurementType.CSD` - Capacitance series (Cs) and dissipation (D)
- `E4890A.MeasurementType.RX` - Resistance (R) and reactance (X)
- `E4890A.MeasurementType.GB` - Conductance (G) and susceptance (B)
- And many more...

#### Properties

**Read/Write:**
- `frequency` - Measurement frequency in Hz (20 - 2,000,000)
- `signal_amplitude` - AC signal amplitude in V (0 - 20) or A (0 - 0.1)
- `bias` - DC bias voltage in V (-40 to 40) or current in A (-0.1 to 0.1)
- `averages` - Number of averages (1 - 256)
- `measurement_time` - MeasurementTime Enum
- `measurement_type` - MeasurementType Enum
- `signal_type` - SignalType Enum
- `alc_enabled` - Automatic level control (bool)

**Read-only:**
- `measurement` - Returns [primary, secondary] values (e.g., [Z, theta])

#### Example Configuration

```python
# Basic impedance measurement
lcr = mm.devices['GPIB0::17::INSTR']

lcr.measurement_time = E4890A.MeasurementTime.MEDIUM
lcr.measurement_type = E4890A.MeasurementType.ZTD
lcr.signal_type = E4890A.SignalType.VOLTAGE
lcr.signal_amplitude = 0.05  # 50 mV
lcr.frequency = 1000  # 1 kHz
lcr.averages = 5
lcr.bias = 0
lcr.alc_enabled = True

# Take measurement
result = lcr.measurement  # Returns [|Z|, θ] for ZTD mode
print(f"Z = {result[0]:.2e} Ω, Phase = {result[1]:.2f}°")
```

---

### HP/Agilent 4291A RF Impedance Analyzer

**Import:**
```python
from nfoinstruments.drivers.lcr import HP4291A
# or
from nfoinstruments import HP4291A
```

**Frequency Range:** 1 MHz - 1.8 GHz

#### Methods

**`measure()`** - Perform measurement and return data array
- Returns: NumPy array with shape (2, num_points)
  - Row 0: Real part
  - Row 1: Imaginary part

**`trigger()`** - Trigger a measurement manually

#### Example Usage

```python
hp4291a = mm.devices['GPIB0::18::INSTR']

# Perform measurement
data = hp4291a.measure()
real_part = data[0]  # Real impedance values
imag_part = data[1]  # Imaginary impedance values

print(f"Measured {len(real_part)} frequency points")
```

#### Notes

- High-frequency impedance measurements (RF range)
- Uses binary data transfer for speed
- Automatic trigger and SRQ handling
- Returns raw data array for flexibility

---

## Temperature Controllers

### Janis Probe Station

**Import:**
```python
from nfoinstruments.drivers.temperature import Janis
```

#### Properties

**Read/Write:**
- `temperature_setpoint` - Target temperature in Kelvin
- `max_heater_power` - Maximum heater power (default 75)

**Read-only:**
- `temperature` - Current temperature in K
- `temperature_stable` - Boolean, True when temperature is stable

#### Example Usage

```python
janis = mm.devices['GPIB0::16::INSTR']

# Set temperature
janis.temperature_setpoint = 300  # 300 K

# Wait for stability
while not janis.temperature_stable:
    current = janis.temperature
    print(f"Stabilizing... Current: {current:.2f} K")
    time.sleep(10)

print(f"Stable at {janis.temperature:.2f} K")
```

#### Stability Criteria

Temperature is considered stable when:
- Current temperature within tolerance of setpoint
- Temperature has been stable for `_temp_stable_time` seconds (default 60s)

---

### PPMS (Physical Property Measurement System)

**Import:**
```python
from nfoinstruments.drivers.temperature import PPMS
```

#### Properties

**Read/Write:**
- `temperature_setpoint` - Tuple: (temp_K, rate_K/min, mode)
  - Mode: `'fast settle'` or `'no overshoot'`
- `field_setpoint` - Tuple: (field_Oe, rate_Oe/sec, mode, ???)
- `chamber` - Chamber state (0-4)

**Read-only:**
- `temperature` - Current temperature in K
- `temperature_stable` - Boolean
- `field_stable` - Boolean
- `sample_position` - Current sample position status

#### Chamber Control Methods

- `seal()` - Seal the chamber
- `purge()` - Purge with helium
- `vent_seal()` - Vent and seal (checks temperature 290-320K)
- `pump()` - Pump down
- `vent_continuous()` - Continuous vent (checks temperature)

#### Example Usage

```python
ppms = mm.devices['GPIB0::15::INSTR']

# Set temperature with control
ppms.temperature_setpoint = (300, 10, 'fast settle')
# 300 K target, 10 K/min ramp rate, fast settle mode

# Wait for stability
while not ppms.temperature_stable:
    current = ppms.temperature
    print(f"Current: {current:.2f} K")
    time.sleep(5)

# Chamber control
ppms.seal()  # Seal chamber before cooling
ppms.temperature_setpoint = (10, 5, 'no overshoot')
```

#### Safety Notes

- Venting operations check that temperature is between 290-320 K
- Use `seal()` before cooling to cryogenic temperatures
- Use `vent_seal()` or `vent_continuous()` before warming above 320 K

---

## Debugging

### Debug Mode

Test code without hardware:

```python
from nfoinstruments import MeasurementSetup

# Create in debug mode
mm = MeasurementSetup(debug=True)

# No real instruments connected
# Returns dummy data for testing
```

### Print Instrument Status

```python
# LCR meter
lcr.print_status()

# Temperature controller
janis.print_status()
ppms.print_status()
```

### Check Available Devices

```python
mm = MeasurementSetup()
print("Detected instruments:")
for addr in mm.resources:
    print(f"  {addr}")
```

---

## Valid Ranges

### E4890A LCR Meter
- **Frequency:** 20 Hz - 2 MHz
- **Voltage amplitude:** 0 - 20 V
- **Current amplitude:** 0 - 0.1 A
- **DC bias (voltage mode):** -40 to 40 V
- **DC bias (current mode):** -0.1 to 0.1 A
- **Averages:** 1 - 256

### Janis
- **Temperature:** Typically 4 - 325 K (check your system)
- **Max heater power:** Usually 75% (adjustable)

### PPMS
- **Temperature:** 2 - 400 K
- **Temperature rate:** 0 - 20 K/min
- **Magnetic field:** Depends on magnet option

---

## Error Handling

```python
try:
    lcr.frequency = 3000000  # Too high!
except ValueError as e:
    print(f"Invalid frequency: {e}")

try:
    result = lcr.measurement
except Exception as e:
    print(f"Measurement failed: {e}")
    # Retry or skip
```
