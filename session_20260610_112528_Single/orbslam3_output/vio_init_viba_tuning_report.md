# VIO init / VIBA tuning report
Dataset: `session_20260610_112528`; IMU input: CSV `imu_data.csv`; camera/IMU YAML: `raspi_imx219_mono_inertial_noisy_820x616.yaml`.
| case | valid/rows | KFs | path | end error | closure/path | PCA ranges | VIBA1 | VIBA2 | skipped VIBA2 | insufficient excitation | resets |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| `raspi_backendfix_imu_csv_raw_full`<br>raw CSV IMU, default VIBA | 1975/2195 | 70 | 15.132 | 0.138 | 0.00915 | 1.744, 1.164, 0.106 | 1 | 1 | 0 | 0 | 0 |
| `raspi_vio_noisy_skipviba2_full`<br>baseline: raw CSV IMU, skip VIBA2/scale refine | 1975/2195 | 73 | 12.699 | 0.102 | 0.00806 | 1.386, 0.856, 0.133 | 1 | 0 | 1 | 0 | 0 |
| `raspi_vio_lateinit_skipviba2_full`<br>late init: 12s/35KF, skip VIBA2/scale refine | 1975/2195 | 137 | 14.400 | 0.520 | 0.03613 | 2.167, 1.060, 0.115 | 1 | 0 | 1 | 21 | 0 |
| `raspi_vio_early_relaxed_full`<br>early relaxed: 5s/15KF, relaxed excitation, VIBA2 on | 1975/2195 | 71 | 21.786 | 0.142 | 0.00651 | 2.103, 1.353, 0.258 | 1 | 1 | 0 | 0 | 0 |
| `raspi_vio_early_relaxed_skipviba2_full`<br>early relaxed: 5s/15KF, relaxed excitation, skip VIBA2/scale refine | 1975/2195 | 68 | 8.539 | 0.055 | 0.00639 | 0.803, 0.627, 0.125 | 1 | 0 | 1 | 0 | 0 |
| `raspi_vio_relaxed_skipviba2_full`<br>mid relaxed: 8s/20KF, relaxed excitation, skip VIBA2/scale refine | 1975/2195 | 71 | 16.978 | 0.140 | 0.00824 | 1.850, 1.153, 0.149 | 1 | 0 | 1 | 0 | 0 |

## Interpretation
- `raspi_vio_noisy_skipviba2_full` is the previous balanced IMU-on baseline: closure/path 0.00806 and PCA thickness 0.133.
- Very late initialization is worse here: `raspi_vio_lateinit_skipviba2_full` waits until the visual motion window is already weak, hits insufficient excitation many times, and ends with closure/path 0.03613.
- Early relaxed initialization plus VIBA2 has the best closure/path, but the PCA thickness rises to 0.258, so it looks less like a stable planar table loop.
- The new `raspi_vio_early_relaxed_skipviba2_full` isolates VIBA2: skipping VIBA2 lowers thickness from 0.258 to 0.125 and gives the best closure/path in this batch at 0.00639. It also shrinks the XY extent, so treat it as the current best VIO candidate, but remember monocular-VIO scale still needs an external sanity check against the table size.

## Recommendation
Keep CSV IMU and the original `T_b_c1`. For this sequence, keep `RASPI_ORBSLAM3_SKIP_VIBA2=1` and `RASPI_ORBSLAM3_SKIP_SCALE_REFINEMENT=1`; the best current candidate is the 5s / 15KF relaxed excitation run. The next meaningful backend change is a better first-initialization window selection based on accumulated visual baseline/rotation quality, instead of relying only on fixed time/KF thresholds.
