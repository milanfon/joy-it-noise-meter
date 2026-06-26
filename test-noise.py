import msvcrt
import time
from noise_meter import noise_meter, read_db


def stop_requested():
    while msvcrt.kbhit():
        if msvcrt.getch().lower() == b"x":
            return True
    return False


def sleep_until_next_sample(start_time, interval_seconds=1.0):
    deadline = start_time + interval_seconds
    while time.monotonic() < deadline:
        if stop_requested():
            return True
        time.sleep(0.05)
    return False


def main():
    print("sampling every 1s; press x to stop", flush=True)
    with noise_meter(verbose=True) as dev:
        while not stop_requested():
            sample_start = time.monotonic()
            try:
                print(f"dB(A): {read_db(dev):.1f}", flush=True)
            except TimeoutError as err:
                print(f"read timeout: {err}", flush=True)

            if sleep_until_next_sample(sample_start):
                break


if __name__ == "__main__":
    main()
