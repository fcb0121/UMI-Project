# UMI-Project Data Upload

This repository contains the exported `session_*` folders from the local IMU-camera SLAM workspace.

## Storage policy

Small and medium files live directly in GitHub.

Large binary artifacts are tracked externally and are intentionally ignored in this repository:

- `*.bag`
- `*.osa`
- `raw_video.mp4`
- `raw_video.h264`

## External large files

The current externalized set contains 33 files totaling about 1.566 GB.

See [external_data/README.md](external_data/README.md) for the storage layout and [external_data/missing_large_files.csv](external_data/missing_large_files.csv) for the exact file list, sizes, and SHA-256 hashes.
