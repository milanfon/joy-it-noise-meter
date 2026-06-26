# JOY-IT JT-SLM01 Python library and script

Simply Python library and script to use with the __JOY-IT JT-SLM01__ sound level meter.

The repository contains:

- `noise_meter.py`: _reusable library_ code for connecting to the meter and reading measurements.
- `test-noise.py`: interactive script that prints one `dB(A)` reading.

The HID protocol in this project was reverse engineered from the official `EnvironmentalTester.exe` application.

This project was created for my personal use, so most of the features are tailored for it.

## Requirements

- Windows
    - Sorry, the app was currently developed to be used under Windows, but there's possibility I might need Linux or MacOS support in the future.
- Python 3
    - 3.12 used during development
- `hid` Python package
- The JT-SLM01 noise meter connected over USB
- The official SW must not be opened

Install the Python dependency:

```bash
pip install hid
```

or:

```bash
pip install -r requirements.txt
```

## Script usage

Run the interactive sampling script:

```bash
python test-noise.py
```

Expected behavior:

1. The script opens the HID device.
2. It sends the device start command.
3. It prints one `dB(A)` reading per second.
4. Press `x` to stop.

Example output:

```text
sampling every 1s; press x to stop
opening cached path=b'...'
dB(A): 57.6
dB(A): 58.1
dB(A): 57.4
```

## Library Usage

The main entry point is the `noise_meter(...)` context manager.

Example:

```python
from noise_meter import noise_meter, read_db

with noise_meter() as dev:
    print(read_db(dev))
```

Read several samples:

```python
import time

from noise_meter import noise_meter, read_db

with noise_meter() as dev:
    for _ in range(5):
        print(f"dB(A): {read_db(dev):.1f}")
        time.sleep(1)
```

## Public Functions

### `noise_meter(vid=VID, pid=PID, cache_file=PATH_CACHE_FILE, verbose=False)`

Context manager that:

- opens the device
- starts sampling mode
- yields the HID device handle
- closes the device automatically

### `read_db(dev)`

Requests one live measurement from the meter and returns a floating-point `dB(A)` value.

### `open_device(vid=VID, pid=PID, cache_file=PATH_CACHE_FILE, verbose=False)`

Opens the HID device and returns the raw `hid.device()` handle.

This function:

- uses `HID_PATH` if set
- otherwise tries the cached path first
- otherwise falls back to `hid.enumerate(...)`

### `start_sampling(dev)`

Flushes pending packets and sends the device start command.

## HID Path Cache

To avoid slow enumeration on every run, the script stores the last working HID path in:

```text
.noise-meter-hid-path
```

Behavior:

- first run usually enumerates the device
- later runs try the cached path first
- if the cached path fails, the code enumerates again and refreshes the cache

## Environment Override

You can force a specific HID path with the `HID_PATH` environment variable.

PowerShell example:

```powershell
$env:HID_PATH='\\?\HID#VID_2F81&PID_5721#...'
python test-noise.py
```

## Notes

- The script is currently focused on live readings only.
- It does not save history to a file yet.
- If the vendor application is open, it may hold the HID device and block access from Python.
- Startup may still be slower than the vendor application on the first run because `hid.enumerate(...)` on Windows can be slow.