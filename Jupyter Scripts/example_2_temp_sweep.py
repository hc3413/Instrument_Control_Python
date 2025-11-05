"""
Example 2: Temperature Series IS Measurement

Perform impedance spectroscopy at multiple temperatures.
"""

from nfoinstruments.drivers import Janis, E4890A
from nfoinstruments.drivers.setup import MeasurementSetup
from nfoinstruments.procedures import set_temperature_and_wait, sweep_frequency_lcr
import numpy as np

# === Setup ===
mm = MeasurementSetup()
mm.connect_to_devices({
    'GPIB0::16::INSTR': Janis,
    'GPIB0::17::INSTR': E4890A
})

janis = mm.devices['GPIB0::16::INSTR']
lcr = mm.devices['GPIB0::17::INSTR']

# === Measurement Parameters ===
temperature_points = [300, 280, 260, 240, 220, 200]  # K
frequency_points = np.logspace(np.log10(20), np.log10(2e6), 100)  # 20 Hz to 2 MHz
lcr.bias = 0.0  # Set DC bias

run_count = 1  # Starting run number

# === Perform Measurements ===
print(f"Starting temperature sweep: {temperature_points} K")
print("="*60)

for target_temp in temperature_points:
    print(f"\n{'='*60}")
    print(f"Temperature: {target_temp} K")
    print('='*60)
    
    # Set temperature and wait for stability
    actual_temp = set_temperature_and_wait(janis, target_temp, extra_settle_time=30, verbose=True)
    
    # Output filename
    filename = f"data/run{run_count:03d}_temp_{actual_temp:.0f}.csv"
    print(f"\nWriting data to: {filename}")
    
    # Perform frequency sweep
    with open(filename, "w") as f:
        f.write("# time,bias,frequency,NA,Z,theta\n")
        sweep_frequency_lcr(janis, lcr, frequency_points, f, verbose=True)
    
    print(f"✓ Run {run_count} complete!")
    run_count += 1

print("\n" + "="*60)
print("✓ ALL MEASUREMENTS COMPLETE!")
print("="*60)
