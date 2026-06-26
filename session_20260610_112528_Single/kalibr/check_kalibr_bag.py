#!/usr/bin/env python3
"""
Check that a Kalibr ROS bag contains the expected camera and IMU topics and
that their timestamp ranges overlap.

Run inside a ROS environment that provides rosbag.
"""

import argparse
from pathlib import Path

import rosbag


def topic_range(bag, topic):
    count = 0
    first = None
    last = None

    for _, msg, t in bag.read_messages(topics=[topic]):
        stamp = getattr(getattr(msg, "header", None), "stamp", None)
        sec = stamp.to_sec() if stamp is not None and stamp.to_sec() > 0 else t.to_sec()
        if first is None:
            first = sec
        last = sec
        count += 1

    return count, first, last


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bag", required=True, type=Path)
    parser.add_argument("--cam-topic", default="/cam0/image_raw")
    parser.add_argument("--imu-topic", default="/imu0")
    args = parser.parse_args()

    if not args.bag.exists():
        raise SystemExit(f"Bag does not exist: {args.bag}")

    with rosbag.Bag(str(args.bag), "r") as bag:
        info = bag.get_type_and_topic_info()
        topics = set(info.topics)
        missing = [topic for topic in (args.cam_topic, args.imu_topic) if topic not in topics]
        if missing:
            available = "\n".join(f"  - {topic}" for topic in sorted(topics))
            raise SystemExit(
                "Missing expected topic(s): "
                + ", ".join(missing)
                + "\nAvailable topics:\n"
                + available
            )

        cam_count, cam_start, cam_end = topic_range(bag, args.cam_topic)
        imu_count, imu_start, imu_end = topic_range(bag, args.imu_topic)

    if cam_count == 0:
        raise SystemExit(f"No messages on {args.cam_topic}")
    if imu_count == 0:
        raise SystemExit(f"No messages on {args.imu_topic}")

    overlap_start = max(cam_start, imu_start)
    overlap_end = min(cam_end, imu_end)
    overlap = overlap_end - overlap_start

    print(f"Bag: {args.bag}")
    print(f"{args.cam_topic}: {cam_count} messages, {cam_start:.6f} -> {cam_end:.6f}")
    print(f"{args.imu_topic}: {imu_count} messages, {imu_start:.6f} -> {imu_end:.6f}")
    print(f"Overlap: {overlap:.6f} seconds")

    if overlap <= 0:
        raise SystemExit("Camera and IMU timestamp ranges do not overlap")

    print("Bag check passed")


if __name__ == "__main__":
    main()
