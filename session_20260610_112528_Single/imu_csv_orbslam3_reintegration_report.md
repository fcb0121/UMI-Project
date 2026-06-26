# ORB-SLAM3 CSV IMU reintegration report

Dataset: `session_20260610_112528`

## Runs

### visual_IMU_mode_noinit

- prefix: `raspi_backendfix_full`
- valid poses: 1975 / 2195
- first/last valid frame: 220 / 2194
- keyframes marked in trajectory: 68
- PCA ranges: 0.161412, 0.072411, 0.028660
- singular ratios: 1.0000, 0.5692, 0.1189
- start/end distance: 0.001236
- VIBA1 started: False
- VIBA2 started: False
- insufficient-excitation messages: 0
- delayed-init messages: 0

### imu_csv_raw

- prefix: `raspi_backendfix_imu_csv_raw_full`
- valid poses: 1975 / 2195
- first/last valid frame: 220 / 2194
- keyframes marked in trajectory: 70
- PCA ranges: 1.744064, 1.163671, 0.106190
- singular ratios: 1.0000, 0.6295, 0.0213
- start/end distance: 0.138441
- VIBA1 started: True
- VIBA2 started: True
- insufficient-excitation messages: 0
- delayed-init messages: 30

### imu_csv_shift_minus0455

- prefix: `raspi_backendfix_imu_csv_shift0455_full`
- valid poses: 1975 / 2195
- first/last valid frame: 220 / 2194
- keyframes marked in trajectory: 54
- PCA ranges: 0.159598, 0.072971, 0.026844
- singular ratios: 1.0000, 0.5258, 0.1333
- start/end distance: 0.000664
- VIBA1 started: False
- VIBA2 started: False
- insufficient-excitation messages: 127
- delayed-init messages: 30

## Interpretation

- Raw CSV IMU input successfully reaches ORB-SLAM3 inertial initialization and starts VIBA1/VIBA2. This is the first run here where IMU is actually accepted by the backend.
- The `-45.5 ms` shifted CSV does not initialize; it repeatedly reports insufficient visual/IMU excitation. In this wrapper, the raw CSV timing is therefore the better next baseline.
- Raw CSV changes trajectory scale from the tiny visual-only scale to roughly meter-scale motion, but the closure is worse than the pure visual keyframe loop. This means IMU is usable, but the VIO configuration still needs tuning before it is the final table map.

## Useful outputs

- raw CSV trajectory/map: `orbslam3_output/raspi_backendfix_imu_csv_raw_full_map_plus_trajectory_color.ply`
- raw CSV PCA SVG: `orbslam3_output/raspi_backendfix_imu_csv_raw_full_trajectory_pca.svg`
- shifted CSV trajectory/map: `orbslam3_output/raspi_backendfix_imu_csv_shift0455_full_map_plus_trajectory_color.ply`
- shifted CSV PCA SVG: `orbslam3_output/raspi_backendfix_imu_csv_shift0455_full_trajectory_pca.svg`
