# ORB-SLAM3 PnP fallback threshold-25 noreset result

- valid poses: 642
- first/last frame: 1553 / 2194
- first/last time: 51.757 / 73.120 s
- map points: 1521
- xyz ranges: 0.393959, 0.255867, 1.144078
- PCA ranges: 1.133983, 0.244160, 0.238667
- path length: 37.856169
- PCA top-view path length: 24.116126
- start-end distance: 1.141134
- closure ratio: 0.030144

Interpretation:
- This run proves the frozen-trajectory issue was caused by the g2o PoseOptimization path, not by the camera being static.
- Tracking is still weak because most frames are marked lost; this is not yet a final table reconstruction.
