# ORB-SLAM3 PnP fallback threshold-25 result

- valid poses: 1686
- first/last frame: 509 / 2194
- first/last time: 16.963 / 73.120 s
- map points: 2198
- xyz ranges: 10.226794, 13.901038, 88.010103
- PCA ranges: 88.382074, 5.773639, 5.723284
- path length: 9541.084852
- PCA top-view path length: 6075.231561
- start-end distance: 88.561670
- closure ratio: 0.009282

Interpretation:
- This run proves the frozen-trajectory issue was caused by the g2o PoseOptimization path, not by the camera being static.
- Tracking is still weak because most frames are marked lost; this is not yet a final table reconstruction.
