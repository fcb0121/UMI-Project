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
      --output_keyframe_tum ${OUT}/raspi_backend_final_stable_full_keyframes_tum.txt \
      --output_map_points_ply ${OUT}/raspi_backend_final_stable_full_mappoints.ply \
      --output_map_points_xyz ${OUT}/raspi_backend_final_stable_full_mappoints.xyz \
      --output_trajectory_csv ${OUT}/raspi_backend_final_stable_full_traj.csv \
      --save_map ${OUT}/raspi_backend_final_stable_full_atlas.osa" \
  > "${OUT}/raspi_backend_final_stable_full_stdout.log" \
  2> "${OUT}/raspi_backend_final_stable_full_stderr.log"

