# Measurement Guide

This guide shows how to use the instrument classes and procedures for stacked measurements.

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Single Measurements](#single-measurements)
3. [Stacked Measurements](#stacked-measurements)
4. [Advanced Examples](#advanced-examples)

---

## Basic Setup

### Import Required Modules

```python
from nfoinstruments.drivers import Janis, E4890A
from nfoinstruments.drivers.setup import MeasurementSetup
from nfoinstruments.procedures import (
    set_temperature_and_wait, 
    sweep_frequency_lcr,
    set_bias_and_wait
)
import numpy as np
```

### Connect to Instruments

```python
# Create setup and connect
mm = MeasurementSetup()
mm.connect_to_devices({
    'GPIB0::16::INSTR': Janis,      # Temperature controller
    'GPIB0::17::INSTR': E4890A      # LCR meter
})

# Get instrument handles
janis = mm.devices['GPIB0::16::INSTR']
lcr = mm.devices['GPIB0::17::INSTR']
```

### Configure LCR Meter

```python
# Use Enums for type safety!
lcr.measurement_type = E4890A.MeasurementType.ZTD      # Z and theta (impedance)
lcr.measurement_time = E4890A.MeasurementTime.MEDIUM   # Medium integration time
lcr.signal_amplitude = 0.05                             # 50 mV AC signal
lcr.averages = 5                                        # Average 5 measurements
lcr.bias = 0.0                                          # No DC bias
```

**Available Measurement Types:**
- `ZTD` - Impedance magnitude and phase (most common)
- `RX` - Resistance and reactance
- `CPD` - Capacitance (parallel) and dissipation
- `CSD` - Capacitance (series) and dissipation

---

## Single Measurements

### Example 1: Single Temperature, Frequency Sweep

```python
# Set temperature
target_temp = 300  # Kelvin
actual_temp = set_temperature_and_wait(janis, target_temp, extra_settle_time=30, verbose=True)

# Create frequency array
frequencies = np.logspace(np.log10(20), np.log10(2e6), 100)  # 20 Hz to 2 MHz, 100 points

# Perform measurement and save
filename = f"data_T{actual_temp:.0f}.csv"
with open(filename, "w") as f:
    f.write("# time,bias,frequency,NA,Z,theta\n")
    sweep_frequency_lcr(janis, lcr, frequencies, f, verbose=True)

print(f"✓ Data saved to {filename}")
```

### Example 2: Single Temperature, Single Frequency

```python
# Set temperature
set_temperature_and_wait(janis, 300, extra_settle_time=30)

# Single measurement at specific frequency
lcr.frequency = 1000  # 1 kHz
result = lcr.measurement  # Returns [Z, theta] for ZTD mode

print(f"Impedance: {result[0]:.2e} Ω")
print(f"Phase: {result[1]:.2f}°")
```

---

## Stacked Measurements

### Example 3: Temperature Sweep (Frequency Sweep at Each Temperature)

```python
# Define temperature and frequency points
temperature_points = [300, 280, 260, 240, 220, 200]  # Kelvin
frequencies = np.logspace(np.log10(20), np.log10(2e6), 100)

# Configure LCR meter
lcr.bias = 0.0
lcr.signal_amplitude = 0.05

# Loop over temperatures
for i, target_temp in enumerate(temperature_points, start=1):
    print(f"\n{'='*60}")
    print(f"Temperature {i}/{len(temperature_points)}: {target_temp} K")
    print('='*60)
    
    # Set temperature and wait for stability
    actual_temp = set_temperature_and_wait(janis, target_temp, extra_settle_time=30, verbose=True)
    
    # Perform frequency sweep
    filename = f"data/run{i:03d}_T{actual_temp:.0f}.csv"
    with open(filename, "w") as f:
        f.write("# time,bias,frequency,NA,Z,theta\n")
        sweep_frequency_lcr(janis, lcr, frequencies, f, verbose=True)
    
    print(f"✓ Saved: {filename}")

print("\n✓ Temperature sweep complete!")
```

### Example 4: Bias Sweep at Each Temperature

```python
# Define points
temperature_points = [300, 280, 260]
bias_points = [-1.0, -0.5, 0.0, 0.5, 1.0]  # Volts
frequencies = np.logspace(np.log10(20), np.log10(2e6), 50)

run_count = 1

# Loop over temperatures
for target_temp in temperature_points:
    print(f"\n{'='*60}")
    print(f"Temperature: {target_temp} K")
    print('='*60)
    
    actual_temp = set_temperature_and_wait(janis, target_temp, extra_settle_time=30, verbose=True)
    
    # Loop over bias voltages
    for bias in bias_points:
        print(f"\n  Bias: {bias} V")
        
        # Set bias and wait
        set_bias_and_wait(lcr, bias, settle_time=1.0)
        
        # Perform frequency sweep
        filename = f"data/run{run_count:03d}_T{actual_temp:.0f}_V{bias:+.1f}.csv"
        with open(filename, "w") as f:
            f.write("# time,bias,frequency,NA,Z,theta\n")
            sweep_frequency_lcr(janis, lcr, frequencies, f, verbose=True)
        
        print(f"  ✓ Saved: {filename}")
        run_count += 1

print("\n✓ All measurements complete!")
```

---

## Advanced Examples

### Example 5: Multiple Frequency Ranges

Sometimes you want different frequency spacings in different ranges:

```python
# Create frequency array with more points at low frequencies
low_freq = np.logspace(np.log10(20), np.log10(1000), 50)      # 20 Hz - 1 kHz (50 pts)
mid_freq = np.logspace(np.log10(1000), np.log10(100e3), 30)   # 1 kHz - 100 kHz (30 pts)
high_freq = np.logspace(np.log10(100e3), np.log10(2e6), 20)   # 100 kHz - 2 MHz (20 pts)

frequencies = np.unique(np.concatenate([low_freq, mid_freq, high_freq]))

# Use as normal
actual_temp = set_temperature_and_wait(janis, 300, extra_settle_time=30)
with open("detailed_sweep.csv", "w") as f:
    f.write("# time,bias,frequency,NA,Z,theta\n")
    sweep_frequency_lcr(janis, lcr, frequencies, f, verbose=True)
```

### Example 6: Custom Settling Checks

```python
def wait_for_extra_stable_temperature(temp_controller, target_temp, tolerance=0.05):
    """Wait for temperature to be very stable (within 0.05 K)."""
    
    print(f"Setting temperature to {target_temp} K...")
    temp_controller.temperature_setpoint = target_temp
    
    # First wait for standard stability
    while not temp_controller.temperature_stable:
        time.sleep(10)
    
    # Then check that it stays stable
    print("Checking extra stability...")
    for _ in range(6):  # Check 6 times over 1 minute
        temp = temp_controller.temperature
        if abs(temp - target_temp) > tolerance:
            print(f"  Temperature drifted to {temp:.3f} K, waiting...")
            time.sleep(30)
            continue
        time.sleep(10)
    
    final_temp = temp_controller.temperature
    print(f"✓ Temperature stable at {final_temp:.3f} K")
    return final_temp

# Use it
actual_temp = wait_for_extra_stable_temperature(janis, 77, tolerance=0.05)
```

### Example 7: Live Data Display During Measurement

```python
import matplotlib.pyplot as plt

def sweep_with_plotting(temp_controller, lcr, frequencies, output_file):
    """Frequency sweep with live plotting."""
    
    # Setup plot
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    freq_list = []
    z_list = []
    theta_list = []
    
    for freq in frequencies:
        lcr.frequency = freq
        time.sleep(0.05)
        
        result = lcr.measurement
        curr_temp = temp_controller.temperature
        
        # Save data
        data = f"{time.time()},{lcr.bias},{freq},-1,{result[0]},{result[1]},\n"
        output_file.write(data)
        output_file.flush()
        
        # Update plot
        freq_list.append(freq)
        z_list.append(result[0])
        theta_list.append(result[1])
        
        ax1.clear()
        ax1.loglog(freq_list, z_list, 'b.-')
        ax1.set_xlabel('Frequency (Hz)')
        ax1.set_ylabel('|Z| (Ω)')
        ax1.grid(True)
        
        ax2.clear()
        ax2.semilogx(freq_list, theta_list, 'r.-')
        ax2.set_xlabel('Frequency (Hz)')
        ax2.set_ylabel('Phase (°)')
        ax2.grid(True)
        
        plt.pause(0.01)
    
    plt.ioff()
    plt.show()

# Use it
actual_temp = set_temperature_and_wait(janis, 300, extra_settle_time=30)
frequencies = np.logspace(np.log10(20), np.log10(2e6), 100)

with open("data_with_plot.csv", "w") as f:
    f.write("# time,bias,frequency,NA,Z,theta\n")
    sweep_with_plotting(janis, lcr, frequencies, f)
```

---

## Tips and Best Practices

### Temperature Control

1. **Always wait for stability**: Use `set_temperature_and_wait()` rather than setting temperature directly
2. **Add extra settling time**: Thermal equilibrium can take longer than electrical stability (30-60s recommended)
3. **Check max heater power**: For Janis, ensure `max_heater_power` is appropriate (usually 50-75%)

```python
# Set reasonable heater power for Janis
janis.max_heater_power = 60  # %
```

### LCR Measurements

1. **Use Enums**: Always use `E4890A.MeasurementType.ZTD` not string `'ZTD'`
2. **Settling time**: Add small delays after changing frequency/bias
3. **Averaging**: Increase `lcr.averages` for noisy measurements

```python
# Good practice
lcr.averages = 10  # More averaging for low signal
lcr.measurement_time = E4890A.MeasurementTime.LONG  # Longer integration
```

### File Management

1. **Create data directory first**: 

```python
import os
os.makedirs('data', exist_ok=True)
```

2. **Use consistent naming**: 

```python
filename = f"data/run{run_number:03d}_T{temp:.0f}_V{bias:+.1f}.csv"
```

3. **Add metadata in header**:

```python
with open(filename, "w") as f:
    f.write(f"# Measurement date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"# Temperature: {actual_temp:.2f} K\n")
    f.write(f"# Signal amplitude: {lcr.signal_amplitude} V\n")
    f.write("# time,bias,frequency,NA,Z,theta\n")
```

### Error Handling

```python
try:
    # Your measurement code
    actual_temp = set_temperature_and_wait(janis, 300, extra_settle_time=30)
    
    with open(filename, "w") as f:
        f.write("# time,bias,frequency,NA,Z,theta\n")
        sweep_frequency_lcr(janis, lcr, frequencies, f, verbose=True)
        
except KeyboardInterrupt:
    print("\n⚠ Measurement interrupted by user")
    # Safe shutdown
    lcr.bias = 0.0
    
except Exception as e:
    print(f"❌ Error: {e}")
    # Log error, safe shutdown
    lcr.bias = 0.0
    raise

finally:
    print("Measurement ended")
```

---

## Windows vs macOS Differences

The code is designed to work on both platforms, but keep in mind:

### File Paths

Always use `pathlib` or forward slashes:

```python
from pathlib import Path

# ✓ Good (cross-platform)
data_dir = Path("data")
filename = data_dir / f"run{i:03d}.csv"

# ✗ Bad (Windows-only)
filename = "data\\run001.csv"
```

### GPIB Addresses

Windows may use different GPIB board numbers:

```python
# macOS
addresses = {
    'GPIB0::16::INSTR': Janis,
    'GPIB0::17::INSTR': E4890A
}

# Windows (if using different board)
addresses = {
    'GPIB1::16::INSTR': Janis,  # Note: board 1
    'GPIB1::17::INSTR': E4890A
}
```

Check your system's GPIB configuration with NI MAX (Windows) or NI-VISA Interactive Control (macOS).

---

## Troubleshooting

### "Instrument not responding"

1. Check GPIB addresses with NI-VISA or Keysight Connection Expert
2. Verify cables and power
3. Test with simpler query: `mm.devices['GPIB0::16::INSTR'].resource.query('*IDN?')`

### "Temperature not stabilizing"

1. Check heater power settings
2. Verify thermal connections
3. Allow more settling time
4. Check for thermal shorts or opens

### "Noisy measurements"

1. Increase averaging: `lcr.averages = 10`
2. Use longer integration: `lcr.measurement_time = E4890A.MeasurementTime.LONG`
3. Check grounding and shielding
4. Verify signal amplitude is appropriate

---

## Need Help?

- Check documentation in `instrument-interfaces/docs/`
- See example scripts in `Jupyter Scripts/`
- Check instrument manuals for parameter ranges
