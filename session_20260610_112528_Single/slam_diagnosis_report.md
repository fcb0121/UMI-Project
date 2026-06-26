# session_20260610_112528 SLAM diagnosis

## Data

- Video is readable: 2195 frames, 1640x1232, about 73.12 s.
- IMU is readable: 18292 samples, about 250 Hz.
- The camera now sees the table and AprilGrid for much of the sequence. This capture is qualitatively much better than the previous forward-looking walk.

## Kalibr

- Bag creation succeeded: 2195 images and 18292 IMU messages.
- Kalibr failed before optimization: `No corners could be extracted for camera /cam0/image_raw`.
- I also checked frame `preview/frame_1097.jpg`: the board is visible, but OpenCV marker detection also detects 0 markers.
- Likely cause: the AprilGrid tags are too small in the fisheye full-frame image and/or the printed tag family does not match Kalibr's expected AprilTag family. This does not prove the camera/IMU data is bad; it means this dataset is not usable as a Kalibr cam-IMU calibration sequence.

## OpenVINS

- No-ZUPT output exists: `openvins_output/traj_openvins_nozupt.txt`.
- No-ZUPT showed motion, but with strong drift and large vertical extent. It is not a clean table loop.
- ZUPT output exists: `openvins_output/traj_openvins_zupt.txt`.
- ZUPT collapsed the motion into a tiny path, so it is not appropriate for this continuous walking-around-table sequence.

## ORB-SLAM3

Default mono-inertial run:

- Output trajectory: `orbslam3_output/raspi_table_traj.csv`.
- 2195 rows, 220 lost/invalid rows, 1975 nonzero rows.
- Only 2 unique pose values after initialization, so the camera pose is effectively frozen.
- Map export succeeded, but the map is not trustworthy as a table reconstruction because the camera trajectory did not move.
- Log repeats `skipping early PoseOptimization` 3948 times.

IMU-init experiment:

- Output trajectory: `orbslam3_output/raspi_table_imuinit_traj.csv`.
- Same frozen-trajectory behavior: 2195 rows, 220 lost/invalid rows, 1975 nonzero rows, only 2 unique pose values.
- Log reports `InitializeIMU: insufficient excitation` repeatedly. Because the pose is frozen, ORB-SLAM3 only sees about 0.08 units of visual baseline and refuses IMU initialization.

PoseOptimization experiment:

- I added an environment-variable switch in `orbslam3_ws/ORB_SLAM3/src/Tracking.cc`: `RASPI_ORBSLAM3_SKIP_EARLY_POSE_OPT=0`.
- With early PoseOptimization restored, ORB-SLAM3 crashes in g2o `Optimizer::PoseOptimization`.
- Pure monocular mode also crashes in the same g2o pose optimization path.

## Conclusion

The current blocker is not mainly the new data collection. The new capture is much closer to what we want visually. The blocker is the current SLAM implementation path:

- If PoseOptimization is skipped, ORB-SLAM3 does not crash but freezes the trajectory.
- If PoseOptimization is enabled, ORB-SLAM3 crashes in g2o.
- OpenVINS can produce motion, but it drifts too much for a reliable table-shaped point cloud with the current configuration.

## Recommended next step

For the next practical attempt, do not spend another capture first. Fix the SLAM backend path first:

1. Stabilize ORB-SLAM3 `Optimizer::PoseOptimization` for this fisheye sequence, or run a clean upstream ORB-SLAM3 monocular fisheye build without the local Raspberry Pi crash-avoidance patches.
2. Once monocular fisheye produces a moving trajectory, then re-enable IMU only after visual tracking is healthy.
3. For Kalibr, record a separate calibration sequence with the AprilGrid much closer and larger in frame, moving the camera slowly with roll/pitch/yaw excitation. The current around-table video is good for mapping, but not good for Kalibr corner extraction.

## Backend repair attempt

I added an experimental PnP fallback in ORB-SLAM3:

- `Optimizer::PoseOptimizationPnP(Frame*)`
- enabled with `RASPI_ORBSLAM3_USE_PNP_POSE_OPT=1`
- uses the camera model to unproject fisheye keypoints to normalized rays, then runs OpenCV PnP/RANSAC instead of the crashing g2o pose-only optimizer

I also added:

- `RASPI_ORBSLAM3_MIN_TRACK_INLIERS_UNINIT`, default 50
- a guard in `SaveTrajectoryCSV` for empty-atlas export

Best current run:

- trajectory: `orbslam3_output/raspi_table_pnp_thr25_traj.csv`
- keyframes: `orbslam3_output/raspi_table_pnp_thr25_keyframes_tum.txt`
- point cloud: `orbslam3_output/raspi_table_pnp_thr25_mappoints.ply`
- point cloud xyz: `orbslam3_output/raspi_table_pnp_thr25_mappoints.xyz`
- top-view SVG: `orbslam3_output/raspi_table_pnp_thr25_trajectory_pca.svg`
- quality report: `orbslam3_output/raspi_table_pnp_thr25_quality_report.md`

Result summary:

- valid poses: 1686 / 2195
- lost rows: 509 / 2195
- keyframes: 211
- map points: 2198
- xyz ranges: 10.226794, 13.901038, 88.010103
- PCA ranges: 88.382074, 5.773639, 5.723284

Interpretation:

- The frozen-trajectory failure is now confirmed to be a backend issue, not a static-camera or bad-capture issue.
- Lowering the uninitialized tracking inlier threshold from 50 to 25 greatly reduces resets and lets the trajectory move through most of the video.
- The trajectory still has strong scale/axis drift, so this is not yet the final table-shaped reconstruction.
- Enabling IMU initialization together with the fallback still leads to map reset / backend instability, so IMU should remain disabled until the visual backend is cleaner.

Additional visual-backend experiments:

- `RASPI_ORBSLAM3_PNP_REFINE_INLIERS_ONLY=1` was tested. It made initialization worse and produced an empty final map, so it is not the default.
- `RASPI_ORBSLAM3_DISABLE_UNINIT_LOST_RESET=1` was tested with threshold 25.

Best low-drift local run:

- trajectory: `orbslam3_output/raspi_table_pnp_thr25_noreset_traj.csv`
- keyframes: `orbslam3_output/raspi_table_pnp_thr25_noreset_keyframes_tum.txt`
- point cloud: `orbslam3_output/raspi_table_pnp_thr25_noreset_mappoints.ply`
- point cloud xyz: `orbslam3_output/raspi_table_pnp_thr25_noreset_mappoints.xyz`
- top-view SVG: `orbslam3_output/raspi_table_pnp_thr25_noreset_trajectory_pca.svg`
- quality report: `orbslam3_output/raspi_table_pnp_thr25_noreset_quality_report.md`

Low-drift local result summary:

- valid poses: 642 / 2195
- first/last valid frame: 1553 / 2194
- first/last valid time: 51.757 / 73.120 s
- keyframes: 81
- map points: 1521
- xyz ranges: 0.393959, 0.255867, 1.144078
- PCA ranges: 1.133983, 0.244160, 0.238667

Interpretation:

- The `thr25` run covers more of the sequence but has large scale/axis drift.
- The `thr25_noreset` run covers less of the sequence but is much less exploded, so it is currently the better candidate for visually inspecting a local table point cloud.
- The next visual-backend target should be robust map continuation/relocalization across the middle of the sequence, not IMU initialization yet.

## Plane-stabilized visual trajectory

I added a post-processing diagnostic:

- script: `stabilize_visual_trajectory_plane.py`
- input: ORB-SLAM trajectory CSV + exported sparse map PLY
- method: fit the dominant camera-center motion plane with robust PCA, transform map/trajectory into that coordinate system, and project only the trajectory onto the plane

New CloudCompare outputs:

- low-drift local candidate: `orbslam3_output/raspi_table_pnp_thr25_noreset_plane_map_plus_trajectory_flat.ply`
- low-drift trajectory line: `orbslam3_output/raspi_table_pnp_thr25_noreset_plane_trajectory_flat_polyline.obj`
- low-drift top-view SVG: `orbslam3_output/raspi_table_pnp_thr25_noreset_plane_trajectory_flat_xy.svg`
- long-coverage candidate: `orbslam3_output/raspi_table_pnp_thr25_plane_map_plus_trajectory_flat.ply`
- long-coverage trajectory line: `orbslam3_output/raspi_table_pnp_thr25_plane_trajectory_flat_polyline.obj`
- long-coverage top-view SVG: `orbslam3_output/raspi_table_pnp_thr25_plane_trajectory_flat_xy.svg`

Plane-stabilized result summary:

- `thr25_noreset`: valid poses 642, raw normal-axis range 0.238672, flat XY range 1.133983 x 0.244161, closure/path ratio 0.047242.
- `thr25`: valid poses 1686, raw normal-axis range 5.723406, flat XY range 88.382076 x 5.772985, closure/path ratio 0.014577.

Interpretation:

- The tube-like display is real trajectory drift, not just a CloudCompare rendering artifact.
- Plane projection removes the vertical/normal-axis tube, but the flattened low-drift path is still much more elongated than a physical two-lap table loop should be.
- Therefore the current visual estimate is not only drifting off the motion plane; it is also distorted inside the plane. The next backend fix should target pose optimization / map continuation quality, not only planar visualization.
