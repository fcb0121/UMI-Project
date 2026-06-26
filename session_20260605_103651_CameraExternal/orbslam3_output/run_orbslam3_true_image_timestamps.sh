#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=/home/zzzjt/projects
SESSION=${PROJECT_ROOT}/session_20260605_103651
ORB=${PROJECT_ROOT}/orbslam3_ws/ORB_SLAM3
OUT=${SESSION}/orbslam3_output

docker run --rm \
  -v "${PROJECT_ROOT}:${PROJECT_ROOT}" \
  chicheng/orb_slam3:latest \
  bash -lc "cd ${ORB} && \
    ./Examples/Monocular-Inertial/raspi_mono_inertial_slam \
      --vocabulary ${ORB}/Vocabulary/ORBvoc.txt \
      --setting ${OUT}/raspi_imx219_mono_inertial_noisy_820x616.yaml \
      --input_video ${SESSION}/raw_video.mp4 \
      --input_imu_csv ${SESSION}/imu_data.csv \
      --frame_timestamps_csv ${SESSION}/video_timestamps.csv \
      --output_trajectory_csv ${OUT}/raspi_true_image_ts_csvimu_traj.csv \
      --output_keyframe_tum ${OUT}/raspi_true_image_ts_csvimu_keyframes_tum.txt \
      --output_map_points_ply ${OUT}/raspi_true_image_ts_csvimu_mappoints.ply \
      --output_map_points_xyz ${OUT}/raspi_true_image_ts_csvimu_mappoints.xyz \
      --save_map ${OUT}/raspi_true_image_ts_csvimu_atlas.osa \
      --max_lost_frames 300" \
  > "${OUT}/raspi_true_image_ts_csvimu_stdout.log" \
  2> "${OUT}/raspi_true_image_ts_csvimu_stderr.log"

