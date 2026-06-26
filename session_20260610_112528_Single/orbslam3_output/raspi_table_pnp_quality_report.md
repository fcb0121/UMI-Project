# ORB-SLAM3 PnP fallback result

- valid poses: 423
- first/last frame: 1772 / 2194
- first/last time: 59.056 / 73.120 s
- map points: 943
- xyz ranges: 3.833912, 3.548519, 7.211862
- PCA ranges: 7.182933, 2.938049, 2.846232
- path length: 210.347038
- PCA top-view path length: 133.734613
- start-end distance: 7.620603
- closure ratio: 0.036229

Interpretation:
- This run proves the frozen-trajectory issue was caused by the g2o PoseOptimization path, not by the camera being static.
- Tracking is still weak because most frames are marked lost; this is not yet a final table reconstruction.
