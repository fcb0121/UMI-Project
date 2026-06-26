# WSL + Docker + Kalibr Camera-IMU Extrinsic Calibration

目标：在 WSL 里搭建 Kalibr 环境，并用树莓派采集的 `session_20260605_103651` 完成 Raspberry Pi IMX219 相机和 IMU 的外参标定。

优先使用 Docker/Kalibr，避免污染 WSL 系统环境。WSL 如果是 Ubuntu 20.04，也可以直接安装 ROS Noetic + Kalibr；如果是 Ubuntu 22.04 或 24.04，建议必须用 Docker，因为 ROS Noetic 主要对应 Ubuntu 20.04。

## Data

本目录就是采集会话：

```text
session_20260605_103651/
  raw_video.mp4
  video_timestamps.csv
  imu_data.csv
  imu_data.json
  kalibr/
```

建议在 WSL 中放到：

```bash
mkdir -p ~/kalibr_data
cp -a /path/to/session_20260605_103651 ~/kalibr_data/
cd ~/kalibr_data/session_20260605_103651
```

如果数据在 Windows 盘里，建议先拷贝到 WSL 的 Linux 文件系统中再跑，避免 Docker 读取 `/mnt/c/...` 时性能很差。

## Build Kalibr Docker Image

```bash
cd ~/kalibr_data/session_20260605_103651
./kalibr/run_kalibr_docker.sh build
```

这会构建 `kalibr:ros1-20.04`，基于 Ubuntu 20.04 / ROS Noetic 编译 Kalibr。首次构建会下载依赖并从源码编译，时间会比较长。

## Generate ROS Bag

```bash
./kalibr/run_kalibr_docker.sh bag
```

生成：

```text
kalibr/session_20260605_103651.bag
```

等价于在 Kalibr/ROS 环境中手动执行：

```bash
cd ~/kalibr_data/session_20260605_103651/kalibr
python3 make_kalibr_bag.py \
  --session ~/kalibr_data/session_20260605_103651 \
  --output ~/kalibr_data/session_20260605_103651/kalibr/session_20260605_103651.bag
```

注意：

- `imu_data.csv` 里的 gyro 单位是 `deg/s`
- `make_kalibr_bag.py` 已经把 gyro 转成 `rad/s`
- 相机 topic: `/cam0/image_raw`
- IMU topic: `/imu0`

## Check Bag

```bash
./kalibr/run_kalibr_docker.sh check
```

检查项：

- bag 里存在 `/cam0/image_raw`
- bag 里存在 `/imu0`
- 两个 topic 的时间戳范围有重叠

也可以进入容器手动看：

```bash
./kalibr/run_kalibr_docker.sh shell
rosbag info /data/kalibr/session_20260605_103651.bag
```

## Run Camera-IMU Calibration

```bash
./kalibr/run_kalibr_docker.sh calibrate --show-extraction
```

等价于在 Kalibr/ROS 环境中手动执行：

```bash
cd ~/kalibr_data/session_20260605_103651/kalibr
kalibr_calibrate_imu_camera \
  --target aprilgrid_6x6_34p5mm.yaml \
  --cam camchain_171453_trial.yaml \
  --imu imu_atk_imu601_approx.yaml \
  --bag session_20260605_103651.bag \
  --show-extraction
```

一口气执行 bag 生成、bag 检查、标定：

```bash
./kalibr/run_kalibr_docker.sh all --show-extraction
```

## Outputs to Inspect

重点看：

- 是否成功检测 AprilGrid
- 是否完成优化
- `T_cam_imu` 或 `T_imu_cam`
- time offset
- 重投影误差
- 生成的 `camchain-imucam*.yaml`
- 生成的 `report*.pdf`

Kalibr 通常会把结果写到运行目录对应的挂载路径中。本 Docker 流程的会话路径在容器内是 `/data`。

## Calibration Files

AprilGrid:

```yaml
tagCols: 6
tagRows: 6
tagSize: 0.0345
tagSpacing: 0.3
```

相机背景：

- Raspberry Pi IMX219
- 分辨率 `1640x1232`
- 视频约 `30 fps`
- 本 session 视频约 `124 s`
- 临时内参来自 `session_20260604_171453`
- `fx ~= 371.878`
- `fy ~= 371.401`
- `cx ~= 824.879`
- `cy ~= 621.730`

IMU 背景：

- 本 session IMU 约 `247 Hz`
- `imu_atk_imu601_approx.yaml` 里的噪声参数是近似值

重要：`camchain_171453_trial.yaml` 是 OpenCV pinhole+rational 临时结果转换成 Kalibr camchain 的参考，不是最终 pinhole-equi 内参。它适合用来打通第一次相机-IMU流程；最终结果建议使用 Kalibr 针对当前相机和镜头生成的相机内参。

## Troubleshooting

如果失败，优先排查：

- Kalibr/ROS 是否安装完整
- `make_kalibr_bag.py` 是否能 import `rosbag`、`rospy`、`sensor_msgs`、`cv_bridge`
- bag 里 topic 名是否是 `/cam0/image_raw` 和 `/imu0`
- bag 中两个 topic 时间戳是否有重叠
- gyro 是否已经转成 `rad/s`
- AprilGrid 参数是否和实际标定板一致
- `camchain_171453_trial.yaml` 是否被 Kalibr 接受
- `--show-extraction` 窗口中 AprilGrid 是否能稳定识别

如果 WSL 图形窗口打不开，先去掉 `--show-extraction` 跑一次；这不会显示提取窗口，但可以判断环境和数据链路是否能跑通。
