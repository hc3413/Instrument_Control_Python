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
    last_check_time = start_time
    warned_no_power = False
    
    while not temp_controller.temperature_stable:
        current = temp_controller.temperature
        elapsed = (time.time() - start_time) / 60
        
        # Check if heater power is stuck at 0 after 2 minutes (for Janis only)
        if hasattr(temp_controller, 'get_controller_status') and not warned_no_power:
            if elapsed > 2.0:  # After 2 minutes
                delta_temp = abs(current - target_temp)
                if delta_temp > 0.3:  # Still far from target
                    try:
                        status = temp_controller.get_controller_status()
                        heater_str = str(status.get('heater_power', 'N/A'))
                        if heater_str != 'N/A' and '0.0' in heater_str:
                            print(f"\nWARNING: Heater power is 0% but {delta_temp:.1f}K from target!")
                            print(f"    Controller mode: {status.get('mode', 'unknown')}")
                            print(f"    Attempting to reactivate temperature control...")
                            temp_controller.temperature_setpoint = target_temp  # Re-send with MODE 2
                            warned_no_power = True
                    except:
                        pass  # Ignore errors in diagnostic check
        
        if verbose:
            print(f"  Current: {current:.2f} K | Target: {target_temp} K | Elapsed: {elapsed:.1f} min", end='\r')
        time.sleep(10)
    
    actual_temp = temp_controller.temperature
    
    if verbose:
        print(f"\nTemperature stable at {actual_temp:.2f} K")
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
        temp_controller: Temperature controller (Janis or PPMS), or None.
                         If None, temperature is recorded as 295.0 K (Room Temp).
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
        
        # Determine temperature to record
        if temp_controller is not None:
            curr_temp = temp_controller.temperature
        else:
            curr_temp = 295.0  # Default to Room Temp if no controller provided
        
        # Format: time,bias,frequency,NA,Z,theta (no trailing comma)
        data = f"{time.time()},{lcr.bias},{freq},-1,{result[0]},{result[1]}\n"
        output_file.write(data)
        output_file.flush()
        
        if verbose and i % 20 == 0:
            print(f"  Progress: {i}/{total_points} points")
    
    if verbose:
        print(f"    Frequency sweep complete ({total_points} points)")


def single_frequency_time_scan(temp_controller, lcr, frequency, duration, output_file, verbose=False):
    """
    Measure at a single frequency for a specified duration to track drift.
    
    The AC signal remains applied continuously throughout the measurement.
    
    Output format: time,bias,frequency,NA,Z,theta (compatible with legacy format)
    
    Args:
        temp_controller: Temperature controller (Janis or PPMS), or None.
        lcr: LCR meter instance
        frequency (float): Frequency to hold (Hz)
        duration (float): Total time to measure (seconds)
        output_file: Open file handle for writing data
        verbose (bool): Print progress updates
    """
    lcr.frequency = frequency
    time.sleep(0.05)
    
    start_time = time.time()
    next_print = start_time
    count = 0
    
    while (time.time() - start_time) < duration:
        result = lcr.measurement  # Returns [Z, theta]
        
        # Format: time,bias,frequency,NA,Z,theta
        data = f"{time.time()},{lcr.bias},{frequency},-1,{result[0]},{result[1]}\n"
        output_file.write(data)
        output_file.flush()
        count += 1
        
        # Print status every 5 seconds
        if verbose and time.time() > next_print:
            elapsed = time.time() - start_time
            print(f"  Time: {elapsed:.1f}/{duration:.1f}s | Points: {count} | Z: {result[0]:.2e} Ohm", end='\r')
            next_print = time.time() + 5.0
            
    if verbose:
        print(f"\n    Time scan complete: {count} points in {duration:.1f}s")


def build_cv_bias_path(v_min, v_max, v_step):
    """
    Build a CV-style bias trajectory: 0 -> +v_max -> v_min -> 0.

    Args:
        v_min (float): Minimum bias in Volts (must be <= 0)
        v_max (float): Maximum bias in Volts (must be >= 0)
        v_step (float): Absolute step size in Volts (must be > 0)

    Returns:
        list[float]: Ordered bias path including endpoints
    """
    import numpy as np

    if v_step <= 0:
        raise ValueError("v_step must be > 0")
    if v_min > 0:
        raise ValueError("v_min must be <= 0 for 0 -> +max -> min -> 0 path")
    if v_max < 0:
        raise ValueError("v_max must be >= 0 for 0 -> +max -> min -> 0 path")

    step = abs(v_step)

    # Segment 1: 0 -> +v_max
    seg_up = np.arange(0.0, v_max + (step * 0.5), step)

    # Segment 2: +v_max -> v_min (skip repeated v_max)
    seg_down = np.arange(v_max - step, v_min - (step * 0.5), -step)

    # Segment 3: v_min -> 0 (skip repeated v_min)
    seg_return = np.arange(v_min + step, 0.0 + (step * 0.5), step)

    path = np.concatenate([seg_up, seg_down, seg_return]).tolist()
    return [float(v) for v in path]


def sweep_cv_lcr(temp_controller, lcr, frequency, bias_points, output_file,
                 verbose=False, settle_time=0.1):
    """
    Perform a CV sweep at a single fixed frequency and write Cp/Gp data.

    Output format: time,bias,frequency,NA,Cp,Gp

    Args:
        temp_controller: Temperature controller (unused here, kept for API consistency)
        lcr: LCR meter with frequency, bias, and measurement properties
        frequency (float): Fixed measurement frequency in Hz
        bias_points (array-like): Ordered DC bias points in Volts
        output_file: Open file handle for writing data
        verbose (bool): Print progress updates
        settle_time (float): Wait time after setting each bias (seconds)
    """
    lcr.frequency = frequency
    total_points = len(bias_points)

    for i, bias in enumerate(bias_points, start=1):
        lcr.bias = float(bias)
        time.sleep(settle_time)

        result = lcr.measurement  # In CPG mode: [Cp, Gp]
        data = f"{time.time()},{lcr.bias},{frequency},-1,{result[0]},{result[1]}\n"
        output_file.write(data)
        output_file.flush()

        if verbose and (i % 20 == 0 or i == total_points):
            print(f"  Progress: {i}/{total_points} bias points", end='\r')

    if verbose:
        print(f"\n    CV sweep complete ({total_points} points @ {frequency:.3g} Hz)")



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


def load_cv_measurement_files(data_dir, pattern="run*.csv"):
    """
    Load CV CSV files from a directory.

    Expected columns (after comments): time,bias,frequency,NA,Cp,Gp

    Args:
        data_dir (str): Path to data directory
        pattern (str): Glob pattern for files (default: "run*.csv")

    Returns:
        list: List of tuples (filename, dataframe)
    """
    import pandas as pd
    from pathlib import Path

    data_path = Path(data_dir)
    files = sorted(data_path.glob(pattern))

    datasets = []
    for file in files:
        try:
            df = pd.read_csv(
                file,
                comment='#',
                names=['time', 'bias', 'frequency', 'NA', 'Cp', 'Gp'],
                skipinitialspace=True,
            )
            df = df.dropna(axis=1, how='all')
            if not df.empty:
                datasets.append((file.name, df))
        except Exception as e:
            print(f"Warning: Could not load {file.name}: {e}")

    return datasets


def plot_all_measurements(data_dir, pattern="run*.csv", figsize=(14, 10), 
                          show_legend=True, 
                          y_lim_left = None, x_lim_left = None, 
                          y_lim_right = None, x_lim_right = None,
                          ):
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
        show_legend (bool): Whether to display legend (default: True)
        
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
    colors = plt.get_cmap('viridis')(np.linspace(0, 0.9, len(datasets)))
    
    # Plot all files
    for (filename, df), color in zip(datasets, colors):
        # Extract metadata from filename or dataframe
        temp = df['bias'].iloc[0] if 'bias' in df.columns else 0
        label = filename.replace('.csv', '') if show_legend else None
        

        freq = df['frequency']
        Z_mag = df['Z']
        theta = df['theta']

        # Top row: All files overlaid
        ax1.loglog(freq, Z_mag, '-', color=color, linewidth=1.5, 
                   label=label, alpha=0.7)
        ax2.semilogx(freq, theta , '-', color=color, linewidth=1.5,
                    label=label, alpha=0.7)
    
    # Configure top plots (all files)
    ax1.set_xlabel('Frequency (Hz)', fontsize=11)
    ax1.set_ylabel('|Z| (Ω)', fontsize=11)
    ax1.set_title('Impedance Magnitude - All Files', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, which='both')
    if show_legend:
        ax1.legend(fontsize=8, loc='best', framealpha=0.9)
    
    ax2.set_xlabel('Frequency (Hz)', fontsize=11)
    ax2.set_ylabel('Phase θ (°)', fontsize=11)
    ax2.set_title('Phase - All Files', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    if show_legend:
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


    #Set axis limits
    if x_lim_left:
        ax1.x_lim = x_lim_left
    if y_lim_left:
        ax1.y_lim = y_lim_left
    
    if x_lim_right:
        ax2.x_lim = x_lim_right
    if y_lim_right:
        ax2.y_lim = y_lim_right

    
    plt.tight_layout()
    plt.show()
    
    print(f"\nPlotted {len(datasets)} files from {data_dir}")
    return fig, (ax1, ax2, ax3, ax4), datasets


def plot_measurement_comparison(data_dir, file_indices=None, figsize=(14, 5), 
                                show_legend=True):
    """
    Plot specific measurement files for comparison.
    
    Args:
        data_dir (str): Path to data directory
        file_indices (list): List of file indices to plot (None = all files)
        figsize (tuple): Figure size
        show_legend (bool): Whether to display legend (default: True)
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
    colors = plt.get_cmap('tab10')(np.linspace(0, 0.9, len(datasets)))
    
    for (filename, df), color in zip(datasets, colors):
        label = filename.replace('.csv', '') if show_legend else None
        
        ax1.loglog(df['frequency'], df['Z'], '-', color=color, linewidth=2, 
                   label=label, marker='o', markersize=3, alpha=0.7)
        ax2.semilogx(df['frequency'], df['theta'], '-', color=color, linewidth=2,
                    label=label, marker='o', markersize=3, alpha=0.7)
    
    ax1.set_xlabel('Frequency (Hz)', fontsize=12)
    ax1.set_ylabel('|Z| (Ω)', fontsize=12)
    ax1.set_title('Impedance Magnitude Comparison', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, which='both')
    if show_legend:
        ax1.legend(fontsize=10, loc='best')
    
    ax2.set_xlabel('Frequency (Hz)', fontsize=12)
    ax2.set_ylabel('Phase θ (°)', fontsize=12)
    ax2.set_title('Phase Comparison', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    if show_legend:
        ax2.legend(fontsize=10, loc='best')
    
    plt.tight_layout()
    plt.show()


def plot_time_scan_comparison(data_dir, file_indices=None, figsize=(14, 5), 
                              normalise = False,
                              show_legend=True):
    """
    Plot time-domain measurement files (Z and theta vs Time).
    
    Compatible with output from single_frequency_time_scan().
    X-axis is normalized to time elapsed since start of measurement (t - t0).
    
    Args:
        data_dir (str): Path to data directory
        file_indices (list): List of file indices to plot (None = all files)
        figsize (tuple): Figure size
        show_legend (bool): Whether to display legend (default: True)
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    datasets = load_measurement_files(data_dir)
    
    if not datasets:
        print(f"No data files found in {data_dir}")
        return
    
    # Filter datasets that actually look like time scans (i.e. single frequency or labeled as such)
    # For now, we just assume the user is pointing to the right directory.
    
    if file_indices is not None:
        datasets = [datasets[i] for i in file_indices if i < len(datasets)]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    colors = plt.get_cmap('tab10')(np.linspace(0, 0.9, len(datasets)))
    
    for (filename, df), color in zip(datasets, colors):
        label = filename.replace('.csv', '') if show_legend else None
        
        # Calculate elapsed time in seconds relative to start of file
        # 'time' column is typically epoch timestamp
        start_time = df['time'].iloc[0]
        elapsed_time = df['time'] - start_time
        
        if normalise:
            Z_mag = df['Z']/df['Z'].iloc[0]
            theta = df['theta']/df['theta'].iloc[0]
        else:
            Z_mag = df['Z']
            theta = df['theta']

        # Plot Magnitude Drift
        ax1.plot(elapsed_time, Z_mag , '-', color=color, linewidth=1.5, 
                   label=label, alpha=0.8)
        
        # Plot Phase Drift
        ax2.plot(elapsed_time, theta , '-', color=color, linewidth=1.5,
                    label=label, alpha=0.8)
    
    # Configure Magnitude Plot
    ax1.set_xlabel('Elapsed Time (s)', fontsize=12)
    ax1.set_ylabel('|Z| (Ω)', fontsize=12)
    ax1.set_title('Impedance Drift vs Time', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, which='both')
    if show_legend:
        ax1.legend(fontsize=8, loc='best', framealpha=0.9)
    
    # Configure Phase Plot
    ax2.set_xlabel('Elapsed Time (s)', fontsize=12)
    ax2.set_ylabel('Phase θ (°)', fontsize=12)
    ax2.set_title('Phase Drift vs Time', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    if show_legend:
        ax2.legend(fontsize=8, loc='best', framealpha=0.9)
    
    plt.tight_layout()
    plt.show()


def plot_cv_comparison(data_dir, pattern="run*.csv", file_indices=None,
                       figsize=(14, 5), show_legend=True , log_plot = False):
    """
    Plot CV files: Cp and Gp versus Vdc.

    Args:
        data_dir (str): Path to data directory
        pattern (str): Glob pattern for files (default: "run*.csv")
        file_indices (list): List of file indices to plot (None = all files)
        figsize (tuple): Figure size
        show_legend (bool): Whether to display legend (default: True)
    """
    import matplotlib.pyplot as plt
    import numpy as np

    datasets = load_cv_measurement_files(data_dir, pattern=pattern)

    if not datasets:
        print(f"No CV data files found in {data_dir}")
        return

    if file_indices is not None:
        datasets = [datasets[i] for i in file_indices if i < len(datasets)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    colors = plt.get_cmap('tab10')(np.linspace(0, 0.9, len(datasets)))

    for (filename, df), color in zip(datasets, colors):
        label = filename.replace('.csv', '') if show_legend else None

        ax1.plot(df['bias'], df['Cp'], '-', color=color, linewidth=2,
                 label=label, marker='o', markersize=3, alpha=0.8)
        ax2.plot(df['bias'], df['Gp'], '-', color=color, linewidth=2,
                 label=label, marker='o', markersize=3, alpha=0.8)

    ax1.set_xlabel('Vdc (V)', fontsize=12)
    ax1.set_ylabel('Cp (F)', fontsize=12)
    ax1.set_title('Capacitance (Cp) vs Vdc', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    if show_legend:
        ax1.legend(fontsize=8, loc='best', framealpha=0.9)

    ax2.set_xlabel('Vdc (V)', fontsize=12)
    ax2.set_ylabel('Gp (S)', fontsize=12)
    ax2.set_title('Conductance (Gp) vs Vdc', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    if show_legend:
        ax2.legend(fontsize=8, loc='best', framealpha=0.9)

    if log_plot == True:
        ax1.set_yscale('log')
        ax2.set_yscale('log')

    plt.tight_layout()
    plt.show()

