#!/usr/bin/env python3
"""
Convert this UMI-Sample session to a ROS bag for Kalibr.

Run inside a ROS/Kalibr environment that provides:
  rosbag, rospy, sensor_msgs, cv_bridge

Example:
  python3 make_kalibr_bag.py \
    --session /media/robotiq/ext_disk/session_20260605_103651 \
    --output /media/robotiq/ext_disk/session_20260605_103651/kalibr/session_20260605_103651.bag
"""

import argparse
import csv
import math
from pathlib import Path

import cv2
import rosbag
import rospy
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, Imu


def read_video_timestamps(path):
    timestamps = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames == ["timestamp"]:
            for row in reader:
                timestamps.append(float(row["timestamp"]))
        else:
            f.seek(0)
            for row in csv.reader(f):
                if row and row[0] != "timestamp":
                    timestamps.append(float(row[0]))
    return timestamps


def write_images(bag, session, bridge, topic):
    video_path = session / "raw_video.mp4"
    timestamps = read_video_timestamps(session / "video_timestamps.csv")
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    frame_idx = 0
    written = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx >= len(timestamps):
            break
        stamp = rospy.Time.from_sec(timestamps[frame_idx])
        msg = bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        msg.header.stamp = stamp
        msg.header.frame_id = "cam0"
        bag.write(topic, msg, stamp)
        written += 1
        frame_idx += 1

    cap.release()
    if written == 0:
        raise RuntimeError("No video frames were written")
    return written, len(timestamps)


def write_imu(bag, session, topic):
    imu_path = session / "imu_data.csv"
    written = 0
    with open(imu_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stamp = rospy.Time.from_sec(float(row["timestamp"]))
            msg = Imu()
            msg.header.stamp = stamp
            msg.header.frame_id = "imu0"
            msg.linear_acceleration.x = float(row["acc_x"])
            msg.linear_acceleration.y = float(row["acc_y"])
            msg.linear_acceleration.z = float(row["acc_z"])
            msg.angular_velocity.x = math.radians(float(row["gyro_x"]))
            msg.angular_velocity.y = math.radians(float(row["gyro_y"]))
            msg.angular_velocity.z = math.radians(float(row["gyro_z"]))
            bag.write(topic, msg, stamp)
            written += 1
    if written == 0:
        raise RuntimeError("No IMU samples were written")
    return written


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cam-topic", default="/cam0/image_raw")
    parser.add_argument("--imu-topic", default="/imu0")
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    bridge = CvBridge()

    with rosbag.Bag(str(args.output), "w") as bag:
        image_count, timestamp_count = write_images(bag, args.session, bridge, args.cam_topic)
        imu_count = write_imu(bag, args.session, args.imu_topic)

    print(f"Wrote {args.output}")
    print(f"Images: {image_count} frames ({timestamp_count} timestamps)")
    print(f"IMU: {imu_count} samples")


if __name__ == "__main__":
    main()
