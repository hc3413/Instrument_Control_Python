"""
Example 3: Temperature + DC Bias Series IS Measurement

Perform impedance spectroscopy at multiple temperatures and DC bias values.
This is a full 2D parameter sweep: for each temperature, measure at each bias.
"""

from nfoinstruments.drivers import Janis, E4890A
from nfoinstruments.drivers.setup import MeasurementSetup
from nfoinstruments.procedures import set_temperature_and_wait, set_bias_and_wait, sweep_frequency_lcr
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
temperature_points = [300, 250, 200]  # K
bias_points = np.linspace(0, 1, 6)  # 0 to 1V in 0.2V steps
frequency_points = np.logspace(np.log10(20), np.log10(2e6), 100)  # 20 Hz to 2 MHz

run_count = 1  # Starting run number

# === Perform Measurements ===
print(f"Starting 2D sweep:")
print(f"  Temperatures: {temperature_points} K")
print(f"  DC Bias: {bias_points[0]:.2f} to {bias_points[-1]:.2f} V ({len(bias_points)} points)")
print(f"  Total measurements: {len(temperature_points) * len(bias_points)}")
print("="*60)

for target_temp in temperature_points:
    print(f"\n{'='*60}")
    print(f"Temperature: {target_temp} K")
    print('='*60)
    
    # Set temperature and wait for stability (only once per temperature)
    actual_temp = set_temperature_and_wait(janis, target_temp, extra_settle_time=30, verbose=True)
    
    # Loop through bias points at this temperature
    for bias in bias_points:
        print(f"\n  → Bias: {bias:.2f} V")
        
        # Set bias and wait for settling
        set_bias_and_wait(lcr, bias, settle_time=0.5)
        
        # Output filename - matches AgilentIS import regex
        filename = f"data/run{run_count:03d}_temp_{actual_temp:.0f}_bias_{bias:.2f}.csv"
        
        # Perform frequency sweep
        with open(filename, "w") as f:
            f.write("# time,bias,frequency,NA,Z,theta\n")
            sweep_frequency_lcr(janis, lcr, frequency_points, f, verbose=True)
        
        print(f"    ✓ Run {run_count} saved")
        run_count += 1

print("\n" + "="*60)
print("✓ ALL MEASUREMENTS COMPLETE!")
print(f"Total files saved: {run_count - 1}")
print("="*60)
