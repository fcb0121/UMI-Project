#!/usr/bin/env bash
set -u

source /opt/ros/noetic/setup.bash
source /home/zzzjt/projects/openvins_ws/devel/setup.bash

OUT_DIR=/home/zzzjt/projects/session_20260605_103651/openvins_output
CONFIG=/home/zzzjt/projects/openvins_ws/src/open_vins/config/session_20260605_103651/estimator_config_dynamic_ts0_frontend_noisyimu_zupt.yaml
BAG=/home/zzzjt/projects/session_20260605_103651/kalibr/session_20260605_103651.bag

roscore > "${OUT_DIR}/openvins_points_roscore.log" 2>&1 &
ROSCORE_PID=$!
sleep 2

python3 "${OUT_DIR}/record_openvins_points.py" --out-dir "${OUT_DIR}" > "${OUT_DIR}/record_openvins_points.log" 2>&1 &
REC_PID=$!
sleep 1

roslaunch ov_msckf subscribe.launch \
  config_path:="${CONFIG}" \
  max_cameras:=1 \
  use_stereo:=false \
  dobag:=true \
  bag:="${BAG}" \
  dosave:=true \
  dotime:=true \
  path_est:="${OUT_DIR}/traj_estimate_dynamic_ts0_frontend_noisyimu_zupt_pointsrun.txt" \
  path_time:="${OUT_DIR}/traj_timing_dynamic_ts0_frontend_noisyimu_zupt_pointsrun.txt" \
  verbosity:=INFO

STATUS=$?
kill -INT "${REC_PID}" 2>/dev/null || true
wait "${REC_PID}" 2>/dev/null || true
kill -INT "${ROSCORE_PID}" 2>/dev/null || true
wait "${ROSCORE_PID}" 2>/dev/null || true
exit "${STATUS}"
