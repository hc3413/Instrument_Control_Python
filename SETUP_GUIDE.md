# Platform-Specific Setup Guide

This project supports both **macOS** (for development) and **Windows** (for instrument control). Each platform has its own virtual environment.

---

## macOS Setup

### 1. Navigate to Project Directory

```bash
cd /Users/horatiocox/Desktop/Instrument_Control_Python
```

### 2. Activate Virtual Environment

```bash
source venvmac/bin/activate
```

You should see `(venvmac)` in your terminal prompt.

### 3. Verify Installation

```bash
# Test the package import
python -c "from nfoinstruments import E4890A, Janis; print('Installation successful!')"
```

### 4. Run Jupyter Notebook

```bash
jupyter notebook
```

Then open `Jupyter Scripts/Agilent_Janis_Control.ipynb`

### 5. Deactivate When Done

```bash
deactivate
```

---

## Windows Setup

### 1. Navigate to Project Directory

```cmd
cd C:\Users\F110216\Desktop\Instrument_Control_Python
```

### 2. Activate Virtual Environment

```cmd
venv\Scripts\activate
```

You should see `(venv)` in your command prompt.

### 3. Verify Installation

```cmd
python -c "from nfoinstruments import E4890A, Janis; print('Installation successful!')"
```

### 4. Run Jupyter Notebook

```cmd
jupyter notebook
```

Then open `Jupyter Scripts/Agilent_Janis_Control.ipynb`

### 5. Deactivate When Done

```cmd
deactivate
```

---

## Syncing Between Platforms

### On Mac (after making changes):

```bash
cd /Users/horatiocox/Desktop/Instrument_Control_Python
git add -A
git commit -m "Description of changes"
git push origin main
```

### On Windows (to get latest changes):

```cmd
cd C:\Users\F110216\Desktop\Instrument_Control_Python
git pull origin main
```

**Important:** After pulling changes that modify Python code:
1. Restart your Jupyter kernel (Kernel → Restart)
2. Re-run setup cells to reload the updated code
3. No need to reinstall - editable mode (`pip install -e .`) handles it automatically!

---

## Quick Reference

### Which Virtual Environment?

- **macOS**: `venvmac/` (excluded from git)
- **Windows**: `venv/` (excluded from git)

### When to Reinstall

**Yes, reinstall needed:**
- First time setup on a new machine
- Adding new dependencies to `setup.py`
- After someone else changes `setup.py` and you pull

**No reinstall needed:**
- Editing existing `.py` files in `nfoinstruments/`
- Adding new functions to existing modules
- Bug fixes in drivers
- Just restart Jupyter kernel!

### Reinstallation Command

```bash
# macOS
cd instrument-interfaces
source ../venvmac/bin/activate
pip install -e .
```

```cmd
# Windows
cd instrument-interfaces
..\venv\Scripts\activate
pip install -e .
```

---

## Troubleshooting

### "Module not found" error

1. Make sure virtual environment is activated (you see `(venv)` or `(venvmac)` in prompt)
2. Try reinstalling: `cd instrument-interfaces && pip install -e .`
3. Restart Jupyter kernel

### Git says "instrument-interfaces" is modified but won't stage

The nested git repository issue was fixed. If it happens again:

```bash
git rm -r --cached instrument-interfaces
git add instrument-interfaces/
git commit -m "Fix submodule issue"
```

### Timeout errors during measurements

The timeout fix is in the code. If you still see timeouts:
1. Pull latest changes: `git pull origin main`
2. Restart Jupyter kernel
3. The LCR timeout now auto-adjusts based on your settings

### Can't connect to instruments

1. Verify GPIB addresses in cell 3 of the notebook
2. Check instrument cables and power
3. Test with NI-VISA or Keysight Connection Expert

---

## Daily Workflow

### Mac (Development)

```bash
# 1. Activate venv
source venvmac/bin/activate

# 2. Start Jupyter
jupyter notebook

# 3. Edit code, test, commit
git add -A
git commit -m "Your changes"
git push origin main

# 4. Deactivate when done
deactivate
```

### Windows (Measurements)

```cmd
# 1. Pull latest code
git pull origin main

# 2. Activate venv
venv\Scripts\activate

# 3. Start Jupyter
jupyter notebook

# 4. Run measurements

# 5. Deactivate when done
deactivate
```

---

## Package Structure

```
Instrument_Control_Python/
├── instrument-interfaces/          # Core package
│   ├── nfoinstruments/
│   │   ├── drivers/               # Instrument classes
│   │   │   ├── lcr.py            # E4980A, HP4291A
│   │   │   ├── temperature.py    # Janis, PPMS
│   │   │   └── setup.py          # MeasurementSetup
│   │   └── procedures/            # Measurement utilities
│   │       └── utils.py          # Helper functions
│   └── setup.py
│
├── Jupyter Scripts/               # Example notebooks
│   └── Agilent_Janis_Control.ipynb
│
├── venv/                          # Windows venv (git ignored)
├── venvmac/                       # macOS venv (git ignored)
│
├── README.md                      # Project overview
├── SETUP_GUIDE.md                 # This file
└── MEASUREMENT_GUIDE.md           # Usage examples
```

---

## Need Help?

Check the other documentation:
- **README.md** - Project overview and features
- **MEASUREMENT_GUIDE.md** - Detailed measurement examples
- **instrument-interfaces/docs/** - API documentation
