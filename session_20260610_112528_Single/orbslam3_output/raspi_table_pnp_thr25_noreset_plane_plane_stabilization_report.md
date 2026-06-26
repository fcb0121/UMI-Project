# Plane-stabilized visual trajectory

This is a diagnostic post-process. It projects valid camera centers onto the dominant motion plane estimated from the visual trajectory.

- source trajectory: `session_20260610_112528/orbslam3_output/raspi_table_pnp_thr25_noreset_traj.csv`
- source map: `session_20260610_112528/orbslam3_output/raspi_table_pnp_thr25_noreset_mappoints.ply`
- valid poses: 642
- poses used for robust plane fit: 642
- flat XY range: 1.133983, 0.244161
- raw normal-axis range before flattening: 0.238672
- raw normal-axis RMS before flattening: 0.084120
- flat path length: 24.116212
- flat closure distance: 1.139304
- closure/path ratio: 0.047242
- median flat step: 0.041647

Interpretation:

- If the flattened path is still not loop-like, the visual pose estimate is unstable in the table plane too.
- If the flattened path becomes loop-like, the visible tube was mostly normal-axis drift from monocular/PnP backend instability.
- The gray map points are not flattened; they are only transformed into the same plane-aligned coordinates.
