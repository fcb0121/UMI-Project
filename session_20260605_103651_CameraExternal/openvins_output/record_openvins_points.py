#!/usr/bin/env python3
import argparse
import signal
from pathlib import Path

import rospy
import sensor_msgs.point_cloud2 as pc2
from sensor_msgs.msg import PointCloud2


latest = {}
counts = {}


def callback(msg, name):
    points = []
    for p in pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True):
        points.append((float(p[0]), float(p[1]), float(p[2])))
    latest[name] = points
    counts[name] = counts.get(name, 0) + 1


def write_xyz(path, points):
    with path.open("w") as f:
        for x, y, z in points:
            f.write(f"{x:.9f} {y:.9f} {z:.9f}\n")


def write_ply(path, points):
    with path.open("w") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(points)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("end_header\n")
        for x, y, z in points:
            f.write(f"{x:.9f} {y:.9f} {z:.9f}\n")


def save_outputs(out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, points in latest.items():
        write_xyz(out_dir / f"openvins_last_{name}.xyz", points)
        write_ply(out_dir / f"openvins_last_{name}.ply", points)
    with (out_dir / "openvins_points_summary.txt").open("w") as f:
        for name in sorted(set(list(latest.keys()) + list(counts.keys()))):
            f.write(f"{name}: messages={counts.get(name, 0)} points={len(latest.get(name, []))}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    rospy.init_node("openvins_points_recorder", anonymous=True)
    rospy.Subscriber("/ov_msckf/points_slam", PointCloud2, callback, callback_args="slam", queue_size=1)
    rospy.Subscriber("/ov_msckf/points_msckf", PointCloud2, callback, callback_args="msckf", queue_size=1)

    def handle_shutdown(signum, frame):
        save_outputs(args.out_dir)
        rospy.signal_shutdown(f"signal {signum}")

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    rospy.spin()
    save_outputs(args.out_dir)


if __name__ == "__main__":
    main()
