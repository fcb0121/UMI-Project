# External Large Files

This repository uses a split-storage approach:

- GitHub stores the session structure, reports, logs, calibration outputs, plots, and other moderate-size artifacts.
- External storage stores large binary files that are inconvenient to maintain in a normal GitHub repository.

## Current externalized files

- 33 files
- About 1.566 GB total

Per-session summary:

- `session_20260604_171453_CameraInsider`: 2 files, 116.71 MB
- `session_20260605_103651_CameraExternal`: 10 files, 475.91 MB
- `session_20260610_112528_Single`: 11 files, 308.72 MB
- `session_20260615_112658_Single`: 2 files, 135.87 MB
- `session_20260615_132706_Single`: 2 files, 126.99 MB
- `session_20260616_165442_Single`: 2 files, 116.60 MB
- `session_20260617_105637_Single`: 2 files, 186.58 MB
- `session_20260617_113933_Single`: 2 files, 136.45 MB

## Recommended layout

Store the missing large files in an external location while preserving the same relative paths as this repository.

Example root:

- `UMI-Project-large-files/`

Example path under that root:

- `UMI-Project-large-files/session_20260610_112528_Single/raw_video.mp4`

## Verification

Use [missing_large_files.csv](missing_large_files.csv) as the source of truth for:

- relative path
- exact size in bytes
- SHA-256 checksum

Any future upload target can be validated against this manifest before sharing or archiving.
