import csv
import json
import re
from datetime import datetime
from pathlib import Path


def create_log_dir(name, base_dir="out"):
    safe_name = re.sub(r"[^A-Za-z0-9_. -]+", "_", name).strip(" .")
    if not safe_name:
        safe_name = datetime.now().strftime("noise-log-%Y%m%d-%H%M%S")

    path = Path(base_dir) / safe_name
    path.mkdir(parents=True, exist_ok=False)
    return path


def open_csv_log(log_dir):
    csv_path = log_dir / "measurements.csv"
    file = csv_path.open("w", newline="", encoding="utf-8")
    writer = csv.writer(file)
    writer.writerow(["timestamp", "elapsed_seconds", "db_a"])
    file.flush()
    return file, writer


def append_csv_sample(file, writer, started_at, db_a):
    now = datetime.now()
    elapsed_seconds = (now - started_at).total_seconds()
    writer.writerow([now.isoformat(timespec="seconds"), f"{elapsed_seconds:.3f}", f"{db_a:.1f}"])
    file.flush()


def write_summary(log_dir, samples, started_at, finished_at):
    summary_path = log_dir / "summary.json"
    duration_seconds = (finished_at - started_at).total_seconds()

    summary = {
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": finished_at.isoformat(timespec="seconds"),
        "duration_seconds": round(duration_seconds, 3),
        "sample_count": len(samples),
        "min_db_a": None,
        "max_db_a": None,
        "avg_db_a": None,
    }

    if samples:
        summary.update(
            {
                "min_db_a": round(min(samples), 1),
                "max_db_a": round(max(samples), 1),
                "avg_db_a": round(sum(samples) / len(samples), 1),
            }
        )

    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
        file.write("\n")

    return summary_path
