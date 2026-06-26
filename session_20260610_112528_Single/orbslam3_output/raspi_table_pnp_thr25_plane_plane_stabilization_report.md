# Plane-stabilized visual trajectory

This is a diagnostic post-process. It projects valid camera centers onto the dominant motion plane estimated from the visual trajectory.

- source trajectory: `session_20260610_112528/orbslam3_output/raspi_table_pnp_thr25_traj.csv`
- source map: `session_20260610_112528/orbslam3_output/raspi_table_pnp_thr25_mappoints.ply`
- valid poses: 1686
- poses used for robust plane fit: 1686
- flat XY range: 88.382076, 5.772985
- raw normal-axis range before flattening: 5.723406
- raw normal-axis RMS before flattening: 2.021743
- flat path length: 6075.248813
- flat closure distance: 88.561668
- closure/path ratio: 0.014577
- median flat step: 4.003762

Interpretation:

- If the flattened path is still not loop-like, the visual pose estimate is unstable in the table plane too.
- If the flattened path becomes loop-like, the visible tube was mostly normal-axis drift from monocular/PnP backend instability.
- The gray map points are not flattened; they are only transformed into the same plane-aligned coordinates.
