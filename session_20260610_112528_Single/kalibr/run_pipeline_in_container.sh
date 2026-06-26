#!/usr/bin/env bash
set -euo pipefail

source /opt/ros/noetic/setup.bash
source /kalibr_workspace/devel/setup.bash

SESSION_DIR="${SESSION_DIR:-/data}"
SESSION_NAME="${SESSION_NAME:-session}"
BAG_PATH="${BAG_PATH:-${SESSION_DIR}/kalibr/${SESSION_NAME}.bag}"
TARGET_YAML="${TARGET_YAML:-${SESSION_DIR}/kalibr/aprilgrid_6x6_34p5mm.yaml}"
CAM_YAML="${CAM_YAML:-${SESSION_DIR}/kalibr/camchain_171453_trial.yaml}"
IMU_YAML="${IMU_YAML:-${SESSION_DIR}/kalibr/imu_atk_imu601_approx.yaml}"
CAM_TOPIC="${CAM_TOPIC:-/cam0/image_raw}"
IMU_TOPIC="${IMU_TOPIC:-/imu0}"
CAM_MODELS="${CAM_MODELS:-pinhole-equi}"

usage() {
  cat <<EOF
Usage: $0 [bag|check|camera|calibrate|all|shell] [kalibr arguments...]

Commands:
  bag        Convert raw_video.mp4 + CSV timestamps/IMU into a ROS1 bag.
  check      Confirm the bag has expected topics and overlapping timestamps.
  camera     Run kalibr_calibrate_cameras for camera intrinsics.
  calibrate Build the bag if needed, then run kalibr_calibrate_imu_camera.
  all        Build the bag, check it, then run kalibr_calibrate_imu_camera.
  shell      Open a shell with ROS Noetic and Kalibr sourced.

Environment overrides:
  BAG_PATH, TARGET_YAML, CAM_YAML, IMU_YAML, CAM_TOPIC, IMU_TOPIC, CAM_MODELS
EOF
}

make_bag() {
  python3 "${SESSION_DIR}/kalibr/make_kalibr_bag.py" \
    --session "${SESSION_DIR}" \
    --output "${BAG_PATH}" \
    --cam-topic "${CAM_TOPIC}" \
    --imu-topic "${IMU_TOPIC}"
}

check_bag() {
  python3 "${SESSION_DIR}/kalibr/check_kalibr_bag.py" \
    --bag "${BAG_PATH}" \
    --cam-topic "${CAM_TOPIC}" \
    --imu-topic "${IMU_TOPIC}"
}

run_camera_calibration() {
  if [[ ! -f "${BAG_PATH}" ]]; then
    make_bag
  fi

  kalibr_args=(
    --target "${TARGET_YAML}"
    --bag "${BAG_PATH}"
    --models "${CAM_MODELS}"
    --topics "${CAM_TOPIC}"
    "$@"
  )

  cd "${SESSION_DIR}/kalibr"
  if command -v kalibr_calibrate_cameras >/dev/null 2>&1; then
    kalibr_calibrate_cameras "${kalibr_args[@]}"
  else
    rosrun kalibr kalibr_calibrate_cameras "${kalibr_args[@]}"
  fi
}

run_calibration() {
  if [[ ! -f "${BAG_PATH}" ]]; then
    make_bag
  fi

  kalibr_args=(
    --target "${TARGET_YAML}"
    --cam "${CAM_YAML}"
    --imu "${IMU_YAML}"
    --bag "${BAG_PATH}"
    "$@"
  )

  if command -v kalibr_calibrate_imu_camera >/dev/null 2>&1; then
    kalibr_calibrate_imu_camera "${kalibr_args[@]}"
  else
    rosrun kalibr kalibr_calibrate_imu_camera "${kalibr_args[@]}"
  fi
}

command="${1:-calibrate}"
if [[ $# -gt 0 ]]; then
  shift
fi

case "${command}" in
  bag)
    make_bag "$@"
    ;;
  check)
    check_bag "$@"
    ;;
  camera)
    run_camera_calibration "$@"
    ;;
  calibrate)
    run_calibration "$@"
    ;;
  all)
    make_bag
    check_bag
    run_calibration "$@"
    ;;
  shell)
    exec /bin/bash
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown command: ${command}" >&2
    usage >&2
    exit 2
    ;;
esac
