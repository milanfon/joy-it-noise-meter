import os
import time
from contextlib import contextmanager

import hid


VID = 0x2F81
PID = 0x5721
READ_SIZE = 64
READ_TIMEOUT_MS = 1000
START_COMMAND = [0xAA, 0x55, 0x00, 0x03, 0x02]
LIVE_COMMAND = [0xAA, 0x55, 0x01, 0x03, 0x03]
PATH_CACHE_FILE = ".noise-meter-hid-path"


def write_report(dev, payload):
    # The official app prepends report ID 0x00 and writes len(payload) + 1 bytes.
    return dev.write([0x00, *payload])


def read_packet(dev, timeout_ms=READ_TIMEOUT_MS):
    data = dev.read(READ_SIZE, timeout_ms=timeout_ms)
    return list(data) if data else []


def flush_pending(dev, max_packets=10):
    dev.set_nonblocking(True)
    try:
        for _ in range(max_packets):
            if not read_packet(dev, timeout_ms=1):
                break
    finally:
        dev.set_nonblocking(False)


def parse_measurements(data):
    if len(data) >= 5 and data[:2] in ([0xAA, 0x55], [0x55, 0xAA]):
        packet_type = data[2]
        payload_len = data[3]
        checksum_index = payload_len + 1
        checksum = sum(data[:checksum_index]) & 0xFF

        if checksum_index >= len(data):
            raise ValueError(f"truncated framed response: {data}")
        if data[checksum_index] != checksum:
            raise ValueError(
                f"bad checksum: got {data[checksum_index]:02x}, expected {checksum:02x}"
            )
        if packet_type not in (0x01, 0x02):
            raise ValueError(f"unexpected packet type {packet_type:02x}: {data}")

        payload = data[4:checksum_index]
        return [
            payload[i] | (payload[i + 1] << 8)
            for i in range(0, len(payload) - 1, 2)
        ]

    if len(data) >= 2:
        return [(data[0] << 8) | data[1]]

    return []


def measurement_to_db(measurements):
    db_candidates = [value / 100 for value in measurements if 3000 <= value <= 13000]
    if not db_candidates:
        db_candidates = [value / 10 for value in measurements if 300 <= value <= 1300]
    if not db_candidates:
        raise ValueError(f"no plausible dB value in {measurements}")

    return db_candidates[0]


def read_db(dev):
    write_report(dev, LIVE_COMMAND)

    data = []
    for _ in range(5):
        data = read_packet(dev)
        if data:
            break
        write_report(dev, LIVE_COMMAND)

    measurements = parse_measurements(data)
    if not measurements:
        raise TimeoutError("no measurement response from device")

    return measurement_to_db(measurements)


def start_sampling(dev):
    flush_pending(dev)
    write_report(dev, START_COMMAND)
    time.sleep(0.2)


def load_cached_path(cache_file=PATH_CACHE_FILE):
    try:
        with open(cache_file, "rb") as file:
            path = file.read().strip()
    except FileNotFoundError:
        return None

    return path or None


def save_cached_path(path, cache_file=PATH_CACHE_FILE):
    with open(cache_file, "wb") as file:
        file.write(path if isinstance(path, bytes) else path.encode())


def open_device(vid=VID, pid=PID, cache_file=PATH_CACHE_FILE, verbose=False):
    env_path = os.environ.get("HID_PATH")
    if env_path:
        paths = [env_path]
    else:
        cached_path = load_cached_path(cache_file)
        paths = [cached_path] if cached_path else []

    for path in paths:
        dev = hid.device()
        if verbose:
            print(f"opening cached path={path!r}", flush=True)
        try:
            dev.open_path(path)
            return dev
        except OSError as err:
            dev.close()
            if verbose:
                print(f"cached open failed: {err}", flush=True)

    if verbose:
        print(f"enumerating {vid:04x}:{pid:04x}", flush=True)
    devices = hid.enumerate(vid, pid)
    if not devices:
        raise RuntimeError(f"device {vid:04x}:{pid:04x} not found")

    path = devices[0]["path"]
    dev = hid.device()
    if verbose:
        print(f"opening {vid:04x}:{pid:04x} path={path!r}", flush=True)
    dev.open_path(path)
    save_cached_path(path, cache_file)
    return dev


@contextmanager
def noise_meter(vid=VID, pid=PID, cache_file=PATH_CACHE_FILE, verbose=False):
    dev = open_device(vid=vid, pid=pid, cache_file=cache_file, verbose=verbose)
    try:
        start_sampling(dev)
        yield dev
    finally:
        dev.close()
