import argparse
import msvcrt
import time
from datetime import datetime

from noise_log import append_csv_sample, create_log_dir, open_csv_log, write_summary
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


def parse_args():
    parser = argparse.ArgumentParser(description="Read JT-SLM01 noise meter values.")
    parser.add_argument(
        "--csv",
        action="store_true",
        help="write measurements.csv and summary.json under out/<name>",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    csv_file = None
    csv_writer = None
    log_dir = None
    started_at = datetime.now()
    samples = []

    if args.csv:
        log_name = input("Log folder name: ")
        log_dir = create_log_dir(log_name)
        csv_file, csv_writer = open_csv_log(log_dir)
        print(f"logging to {log_dir}", flush=True)

    print("sampling every 1s; press x to stop", flush=True)
    try:
        with noise_meter(verbose=True) as dev:
            started_at = datetime.now()
            while not stop_requested():
                sample_start = time.monotonic()
                try:
                    db_a = read_db(dev)
                    samples.append(db_a)
                    print(f"dB(A): {db_a:.1f}", flush=True)
                    if csv_file is not None:
                        append_csv_sample(csv_file, csv_writer, started_at, db_a)
                except TimeoutError as err:
                    print(f"read timeout: {err}", flush=True)

                if sleep_until_next_sample(sample_start):
                    break
    finally:
        finished_at = datetime.now()
        if csv_file is not None:
            csv_file.close()
        if log_dir is not None:
            summary_path = write_summary(log_dir, samples, started_at, finished_at)
            print(f"summary written to {summary_path}", flush=True)


if __name__ == "__main__":
    main()
