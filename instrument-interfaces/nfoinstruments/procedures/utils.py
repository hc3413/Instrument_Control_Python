"""
Utility functions for impedance spectroscopy measurements.

Provides simple, composable building blocks for temperature control and frequency sweeps.
"""

import time

# =============================================================================
# Core Building Blocks - Use these in your notebooks!
# =============================================================================

def set_temperature_and_wait(temp_controller, target_temp, extra_settle_time=30, verbose=True):
    """
    Set temperature and wait until stable, with optional extra settling time.
    
    Args:
        temp_controller: Temperature controller (Janis or PPMS)
        target_temp (float): Target temperature in Kelvin
        extra_settle_time (float): Additional wait time after stability (seconds)
        verbose (bool): Print status updates
        
    Returns:
        float: Actual temperature reached
    """
    if verbose:
        print(f"Setting temperature to {target_temp} K...")
    
    temp_controller.temperature_setpoint = target_temp
    
    if verbose:
        print("Waiting for temperature stability...")
    
    start_time = time.time()
    while not temp_controller.temperature_stable:
        if verbose:
            current = temp_controller.temperature
            elapsed = (time.time() - start_time) / 60
            print(f"  Current: {current:.2f} K | Target: {target_temp} K | Elapsed: {elapsed:.1f} min", end='\r')
        time.sleep(10)
    
    actual_temp = temp_controller.temperature
    
    if verbose:
        print(f"\n✓ Temperature stable at {actual_temp:.2f} K")
        if extra_settle_time > 0:
            print(f"Additional {extra_settle_time}s settling time...")
    
    time.sleep(extra_settle_time)
    
    return actual_temp


def sweep_frequency_lcr(temp_controller, lcr, frequency_points, output_file, verbose=False):
    """
    Perform frequency sweep and write to file in Agilent legacy format.
    
    This function works with any LCR meter that has `frequency`, `bias`, and `measurement` 
    attributes. The output format is compatible with legacy Agilent data import classes.
    
    Output format: time,bias,frequency,NA,Z,theta (6 columns with trailing comma)
    Header: # time,bias,frequency,NA,Z,theta
    
    Args:
        temp_controller: Temperature controller (Janis or PPMS)
        lcr: LCR meter with frequency, bias, and measurement properties
        frequency_points: Array of frequencies to measure (Hz)
        output_file: Open file handle for writing data
        verbose (bool): Print progress updates
    """
    total_points = len(frequency_points)
    
    for i, freq in enumerate(frequency_points, start=1):
        lcr.frequency = freq
        time.sleep(0.05)  # Small delay for settling
        
        result = lcr.measurement  # Returns [Z, theta] for ZTD mode
        curr_temp = temp_controller.temperature
        
        # Format: time,bias,frequency,NA,Z,theta (no trailing comma)
        data = f"{time.time()},{lcr.bias},{freq},-1,{result[0]},{result[1]}\n"
        output_file.write(data)
        output_file.flush()
        
        if verbose and i % 20 == 0:
            print(f"  Progress: {i}/{total_points} points")
    
    if verbose:
        print(f"  ✓ Frequency sweep complete ({total_points} points)")


def set_bias_and_wait(lcr, bias_voltage, settle_time=0.5):
    """
    Set DC bias and wait for settling.
    
    Args:
        lcr: LCR meter with bias property
        bias_voltage (float): DC bias in Volts
        settle_time (float): Wait time for bias to settle (seconds)
    """
    lcr.bias = bias_voltage
    time.sleep(settle_time)


# =============================================================================
# Legacy Functions - For old measurement_manager-based code
# =============================================================================
# These functions are kept for backwards compatibility with old scripts that use
# the measurement_manager object pattern. They are tightly coupled to a specific
# measurement_manager structure and are NOT recommended for new code.
#
# For new measurements, use the composable building blocks above:
#   - set_temperature_and_wait()
#   - set_bias_and_wait()
#   - sweep_frequency_lcr()
#
# These legacy functions support the old workflow:
#   1. Top-level measurement routines (scan_temp_fixed_biases, bias_sweep_temperature_steps, etc.)
#      that orchestrate full measurement sequences
#   2. Mid-level scan functions (scan_temperature_cont, scan_temperature_step, scan_bias)
#      that iterate over parameter ranges
#   3. Low-level helper (write_measurement_data) that formats and writes data
# =============================================================================

def scan_temp_fixed_biases(measurement_manager, start_temp):
    """
    Full measurement: Temperature scan with fixed bias values.
    
    Loops through each bias point, settles at start temperature, then performs
    either continuous or stepped temperature scanning based on measurement_manager.temperature_mode.
    
    Args:
        measurement_manager: Object with attributes:
            - filename (str): Output file path
            - bias_points (array): DC bias values to measure
            - temperature_mode (str): 'continuous' or 'step'
            - lcr: LCR meter instance
            - ppms: Temperature controller instance
        start_temp (float): Initial temperature to settle at (K)
    """
    with open(measurement_manager.filename, "w") as f:
        for bias in measurement_manager.bias_points:
            settle_at_start_temp(measurement_manager, start_temp)
            measurement_manager.lcr.bias = bias
            if measurement_manager.temperature_mode == 'continuous':
                scan_temperature_cont(measurement_manager, f)
            elif measurement_manager.temperature_mode == 'step':
                scan_temperature_step(measurement_manager, f)
            else:
                raise ValueError("invalid temperature mode")


def bias_sweep_temperature_steps(measurement_manager, start_temp):
    """
    Full measurement: Bias scan at each temperature step.
    
    Settles at start temperature once, then steps through temperature_points,
    performing a bias sweep at each temperature.
    
    Args:
        measurement_manager: Object with attributes:
            - filename (str): Output file path
            - temperature_points (array): Temperature values (K)
            - bias_points (array): DC bias values to scan
            - settle_time (float): Extra settling time after reaching temperature (s)
            - ppms: Temperature controller instance
            - lcr: LCR meter instance
        start_temp (float): Initial temperature to settle at (K)
    """
    settle_at_start_temp(measurement_manager, start_temp)
    with open(measurement_manager.filename, "w") as f:
        for T_point in measurement_manager.temperature_points:
            measurement_manager.ppms.temperature_setpoint = T_point
            while not measurement_manager.ppms.temperature_stable:
                time.sleep(5)
            time.sleep(measurement_manager.settle_time)
            scan_bias(measurement_manager, f)


def freq_sweep_temperature_steps_bias_steps(measurement_manager, start_temp):
    """
    Full measurement: Frequency sweeps at each (temperature, bias) combination.
    
    Nested loops: For each temperature, for each bias, perform frequency sweep.
    Useful for full impedance spectroscopy mapping across T and DC bias.
    
    Args:
        measurement_manager: Object with attributes:
            - filename (str): Output file path
            - temperature_points (array): Temperature values (K)
            - bias_points (array): DC bias values (V)
            - frequency_points (array): Frequency values (Hz)
            - settle_time (float): Extra settling after reaching temperature (s)
            - ppms: Temperature controller instance
            - lcr: LCR meter instance
        start_temp (float): Initial temperature to settle at (K)
    """
    settle_at_start_temp(measurement_manager, start_temp)
    with open(measurement_manager.filename, "w") as f:
        for T_point in measurement_manager.temperature_points:
            print(f'\nChanging temperature to {T_point} K.', flush=True)
            for b_point in measurement_manager.bias_points:
                print(f'Setting bias to {b_point} V.', flush=True)
                measurement_manager.ppms.temperature_setpoint = T_point
                measurement_manager.lcr.bias = b_point 
                time.sleep(0.1)
                while not measurement_manager.ppms.temperature_stable:
                    time.sleep(5)
                time.sleep(measurement_manager.settle_time)
                scan_frequency(measurement_manager, f)


def scan_bias(measurement_manager, f):
    """
    Mid-level: Loop through bias points and write measurements.
    
    Sets each bias value, waits briefly, then writes measurement. Temperature
    and frequency should already be set.
    
    Args:
        measurement_manager: Object with bias_points array and lcr instance
        f (file): Open file handle for writing
    """
    for bias in measurement_manager.bias_points:
        measurement_manager.lcr.bias = bias 
        time.sleep(0.1)
        write_measurement_data(f, measurement_manager)


def scan_frequency(measurement_manager, f, no_ppms=False):
    """
    Mid-level: Loop through frequency points and write measurements.
    
    Sets each frequency, waits briefly, then writes measurement. Temperature
    and bias should already be set.
    
    Args:
        measurement_manager: Object with frequency_points array and lcr instance
        f (file): Open file handle for writing
        no_ppms (bool): If True, don't read temperature from PPMS
    """
    for frequency in measurement_manager.frequency_points:
        measurement_manager.lcr.frequency = frequency
        time.sleep(0.1)
        write_measurement_data(f, measurement_manager, no_ppms=no_ppms)


def scan_temperature_cont(measurement_manager, f):
    """
    Mid-level: Continuous temperature scanning (measure while ramping).
    
    Sets each temperature point and writes measurements continuously while
    temperature approaches target (within 0.5 K tolerance).
    
    Args:
        measurement_manager: Object with temperature_points array and ppms instance
        f (file): Open file handle for writing
    """
    for T_point in measurement_manager.temperature_points:
        measurement_manager.ppms.temperature_setpoint = T_point
        time.sleep(1)
        while True:
            write_measurement_data(f, measurement_manager)
            if abs(measurement_manager.ppms.temperature - 
                   measurement_manager.ppms.temperature_setpoint[0]) < 0.5:
                break


def scan_temperature_step(measurement_manager, f):
    """
    Mid-level: Stepped temperature scanning (wait for stability at each point).
    
    Sets temperature, waits for stability, adds settling time, then writes
    a single measurement.
    
    Args:
        measurement_manager: Object with temperature_points, settle_time, and ppms instance
        f (file): Open file handle for writing
    """
    for T_point in measurement_manager.temperature_points:
        measurement_manager.ppms.temperature_setpoint = T_point
        while not measurement_manager.ppms.temperature_stable:
            time.sleep(5)
        time.sleep(measurement_manager.settle_time)
        write_measurement_data(f, measurement_manager)


def write_measurement_data(f, measurement_manager, no_ppms=False):
    """
    Low-level: Write a single measurement line to file.
    
    Attempts to read from LCR meter (up to 5 retries on error), gets current
    temperature, and writes CSV line.
    
    Format: time,bias,frequency,temperature,Z,theta,
    
    Args:
        f (file): Open file handle for writing
        measurement_manager: Object with lcr and ppms instances
        no_ppms (bool): If True, write -1 for temperature instead of reading from PPMS
    """
    for i in range(5):
        try:
            cap_res = measurement_manager.lcr.get_value()
            break
        except:
            continue
    else:
        return  # All retries failed, skip this measurement
    
    if no_ppms:
        curr_temperature = -1
    else: 
        curr_temperature = measurement_manager.ppms.temperature
        
    data_string = ','.join([str(time.time()), 
                            str(measurement_manager.lcr.bias), 
                            str(measurement_manager.lcr.frequency),
                            str(curr_temperature),
                            str(cap_res[0]),
                            str(cap_res[1]),
                            '\n'])
    f.write(data_string)


def settle_at_start_temp(measurement_manager, start_temp):
    """
    Low-level: Set temperature and wait until stable.
    
    Used to ensure starting temperature is reached before beginning measurements.
    
    Args:
        measurement_manager: Object with ppms instance
        start_temp (float): Target starting temperature (K)
    """
    measurement_manager.ppms.temperature_setpoint = (start_temp, 10, 0)
    while not measurement_manager.ppms.temperature_stable:
        time.sleep(5)


# =============================================================================
# Data Loading and Plotting Utilities
# =============================================================================

def load_measurement_files(data_dir, pattern="run*.csv"):
    """
    Load all measurement CSV files from a directory.
    
    Args:
        data_dir (str): Path to data directory
        pattern (str): Glob pattern for files (default: "run*.csv")
        
    Returns:
        list: List of tuples (filename, dataframe)
    """
    import glob
    import pandas as pd
    from pathlib import Path
    
    data_path = Path(data_dir)
    files = sorted(data_path.glob(pattern))
    
    datasets = []
    for file in files:
        try:
            # Read CSV, skip comment lines, proper column names
            df = pd.read_csv(file, comment='#', 
                           names=['time', 'bias', 'frequency', 'NA', 'Z', 'theta'],
                           skipinitialspace=True)
            # Drop any empty/NaN columns
            df = df.dropna(axis=1, how='all')
            datasets.append((file.name, df))
        except Exception as e:
            print(f"Warning: Could not load {file.name}: {e}")
    
    return datasets


def plot_all_measurements(data_dir, pattern="run*.csv", figsize=(14, 10)):
    """
    Plot all measurement files on the same figure with different colors.
    
    Creates a 2x2 plot showing:
    - Top left: Impedance magnitude vs frequency (all files)
    - Top right: Phase vs frequency (all files)
    - Bottom left: Impedance magnitude (selected file)
    - Bottom right: Phase (selected file)
    
    Args:
        data_dir (str): Path to data directory
        pattern (str): Glob pattern for files (default: "run*.csv")
        figsize (tuple): Figure size (width, height)
        
    Returns:
        fig, axes, datasets
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    datasets = load_measurement_files(data_dir, pattern)
    
    if not datasets:
        print(f"No data files found in {data_dir}")
        return None, None, None
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
    
    # Color map for multiple files
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(datasets)))
    
    # Plot all files
    for (filename, df), color in zip(datasets, colors):
        # Extract metadata from filename or dataframe
        temp = df['bias'].iloc[0] if 'bias' in df.columns else 0
        label = filename.replace('.csv', '')
        
        # Top row: All files overlaid
        ax1.loglog(df['frequency'], df['Z'], '-', color=color, linewidth=1.5, 
                   label=label, alpha=0.7)
        ax2.semilogx(df['frequency'], df['theta'], '-', color=color, linewidth=1.5,
                    label=label, alpha=0.7)
    
    # Configure top plots (all files)
    ax1.set_xlabel('Frequency (Hz)', fontsize=11)
    ax1.set_ylabel('|Z| (Ω)', fontsize=11)
    ax1.set_title('Impedance Magnitude - All Files', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, which='both')
    ax1.legend(fontsize=8, loc='best', framealpha=0.9)
    
    ax2.set_xlabel('Frequency (Hz)', fontsize=11)
    ax2.set_ylabel('Phase θ (°)', fontsize=11)
    ax2.set_title('Phase - All Files', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=8, loc='best', framealpha=0.9)
    
    # Bottom row: Latest file in detail
    latest_file, latest_df = datasets[-1]
    
    ax3.loglog(latest_df['frequency'], latest_df['Z'], 'b-', linewidth=2)
    ax3.set_xlabel('Frequency (Hz)', fontsize=11)
    ax3.set_ylabel('|Z| (Ω)', fontsize=11)
    ax3.set_title(f'Latest: {latest_file}', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, which='both')
    
    ax4.semilogx(latest_df['frequency'], latest_df['theta'], 'r-', linewidth=2)
    ax4.set_xlabel('Frequency (Hz)', fontsize=11)
    ax4.set_ylabel('Phase θ (°)', fontsize=11)
    ax4.set_title(f'Latest: {latest_file}', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    print(f"\n✓ Plotted {len(datasets)} files from {data_dir}")
    return fig, (ax1, ax2, ax3, ax4), datasets


def plot_measurement_comparison(data_dir, file_indices=None, figsize=(14, 5)):
    """
    Plot specific measurement files for comparison.
    
    Args:
        data_dir (str): Path to data directory
        file_indices (list): List of file indices to plot (None = all files)
        figsize (tuple): Figure size
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    datasets = load_measurement_files(data_dir)
    
    if not datasets:
        print(f"No data files found in {data_dir}")
        return
    
    if file_indices is not None:
        datasets = [datasets[i] for i in file_indices if i < len(datasets)]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    colors = plt.cm.tab10(np.linspace(0, 0.9, len(datasets)))
    
    for (filename, df), color in zip(datasets, colors):
        label = filename.replace('.csv', '')
        ax1.loglog(df['frequency'], df['Z'], '-', color=color, linewidth=2, 
                   label=label, marker='o', markersize=3, alpha=0.7)
        ax2.semilogx(df['frequency'], df['theta'], '-', color=color, linewidth=2,
                    label=label, marker='o', markersize=3, alpha=0.7)
    
    ax1.set_xlabel('Frequency (Hz)', fontsize=12)
    ax1.set_ylabel('|Z| (Ω)', fontsize=12)
    ax1.set_title('Impedance Magnitude Comparison', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, which='both')
    ax1.legend(fontsize=10, loc='best')
    
    ax2.set_xlabel('Frequency (Hz)', fontsize=12)
    ax2.set_ylabel('Phase θ (°)', fontsize=12)
    ax2.set_title('Phase Comparison', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10, loc='best')
    
    plt.tight_layout()
    plt.show()
