#!/usr/bin/env python3
import csv
import json
import math
from pathlib import Path


SESSION = Path(__file__).resolve().parent
OUT_DIR = SESSION / "orbslam3_output"


def read_video_timestamps(path):
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return [float(row["timestamp"]) for row in reader]


def read_imu_rows(path):
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def sample(value, cts_ms, date=None):
    data = {"value": value, "cts": cts_ms}
    if date is not None:
        data["date"] = date
    return data


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    video_timestamps = read_video_timestamps(SESSION / "video_timestamps.csv")
    imu_rows = read_imu_rows(SESSION / "imu_data.csv")
    t0 = video_timestamps[0]

    acc_samples = []
    gyro_samples = []
    acc_samples_startzero = []
    gyro_samples_startzero = []

    first = imu_rows[0]
    first_acc = [float(first["acc_x"]), float(first["acc_y"]), float(first["acc_z"])]
    first_gyro = [
        math.radians(float(first["gyro_x"])),
        math.radians(float(first["gyro_y"])),
        math.radians(float(first["gyro_z"])),
    ]
    acc_samples.append(sample(first_acc, 0.0))
    gyro_samples.append(sample(first_gyro, 0.0))

    for row in imu_rows:
        cts_ms = (float(row["timestamp"]) - t0) * 1000.0
        cts_startzero_ms = (float(row["timestamp"]) - float(imu_rows[0]["timestamp"])) * 1000.0
        acc_samples.append(
            sample(
                [float(row["acc_x"]), float(row["acc_y"]), float(row["acc_z"])],
                cts_ms,
            )
        )
        gyro_samples.append(
            sample(
                [
                    math.radians(float(row["gyro_x"])),
                    math.radians(float(row["gyro_y"])),
                    math.radians(float(row["gyro_z"])),
                ],
                cts_ms,
            )
        )
        acc_samples_startzero.append(
            sample(
                [float(row["acc_x"]), float(row["acc_y"]), float(row["acc_z"])],
                cts_startzero_ms,
            )
        )
        gyro_samples_startzero.append(
            sample(
                [
                    math.radians(float(row["gyro_x"])),
                    math.radians(float(row["gyro_y"])),
                    math.radians(float(row["gyro_z"])),
                ],
                cts_startzero_ms,
            )
        )

    cori_samples = [
        sample([1.0, 0.0, 0.0, 0.0], (ts - t0) * 1000.0)
        for ts in video_timestamps
    ]

    payload = {
        "1": {
            "streams": {
                "ACCL": {
                    "samples": acc_samples,
                    "name": "Accelerometer",
                    "units": "m/s^2",
                },
                "GYRO": {
                    "samples": gyro_samples,
                    "name": "Gyroscope",
                    "units": "rad/s",
                },
                "CORI": {
                    "samples": cori_samples,
                    "name": "Camera orientation placeholder",
                    "units": "quaternion",
                },
            }
        }
    }

    out_path = OUT_DIR / "imu_data_orbslam3.json"
    with out_path.open("w") as f:
        json.dump(payload, f, indent=2)
    startzero_payload = {
        "1": {
            "streams": {
                "ACCL": {
                    "samples": acc_samples_startzero,
                    "name": "Accelerometer",
                    "units": "m/s^2",
                },
                "GYRO": {
                    "samples": gyro_samples_startzero,
                    "name": "Gyroscope",
                    "units": "rad/s",
                },
                "CORI": {
                    "samples": sample([1.0, 0.0, 0.0, 0.0], 0.0)
                    and cori_samples,
                    "name": "Camera orientation placeholder",
                    "units": "quaternion",
                },
            }
        }
    }
    startzero_out_path = OUT_DIR / "imu_data_orbslam3_startzero.json"
    with startzero_out_path.open("w") as f:
        json.dump(startzero_payload, f, indent=2)
    print(out_path)
    print(startzero_out_path)
    print(f"video_frames={len(video_timestamps)}")
    print(f"imu_samples={len(imu_rows)}")
    print(f"first_video_ts={t0:.9f}")
    print(f"first_imu_offset_s={float(imu_rows[0]['timestamp']) - t0:.9f}")


if __name__ == "__main__":
    main()
