#!/usr/bin/env python3
import argparse
import csv
from bisect import bisect_left
from pathlib import Path

import cv2
import numpy as np


K = np.array(
    [
        [407.16556289023475, 0.0, 830.9049270734243],
        [0.0, 406.5719721278056, 618.1957669770426],
        [0.0, 0.0, 1.0],
    ],
    dtype=np.float64,
)
D = np.array(
    [
        -0.011925575149450052,
        -0.003951306310202171,
        0.0004051865456881907,
        -0.00030239381530415495,
    ],
    dtype=np.float64,
)
R_CTOI = np.array(
    [
        [0.99995919, -0.00569336, 0.00701395],
        [-0.00712909, -0.02046306, 0.99976519],
        [-0.00554850, -0.99977440, -0.02050282],
    ],
    dtype=np.float64,
)
P_CINI = np.array([-0.03075538, -0.02840403, 0.10322620], dtype=np.float64)


def quat_xyzw_to_rot(q):
    x, y, z, w = q
    n = x * x + y * y + z * z + w * w
    if n < 1e-12:
        return np.eye(3)
    s = 2.0 / n
    xx, yy, zz = x * x * s, y * y * s, z * z * s
    xy, xz, yz = x * y * s, x * z * s, y * z * s
    wx, wy, wz = w * x * s, w * y * s, w * z * s
    return np.array(
        [
            [1.0 - yy - zz, xy - wz, xz + wy],
            [xy + wz, 1.0 - xx - zz, yz - wx],
            [xz - wy, yz + wx, 1.0 - xx - yy],
        ],
        dtype=np.float64,
    )


def read_video_timestamps(path):
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return [float(row["timestamp"]) for row in reader]


def read_traj(path):
    stamps, poses = [], []
    with path.open() as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            vals = [float(x) for x in line.split()]
            t = vals[0]
            p_iing = np.array(vals[1:4], dtype=np.float64)
            q_itog = np.array(vals[4:8], dtype=np.float64)
            r_itog = quat_xyzw_to_rot(q_itog)
            p_cing = p_iing + r_itog @ P_CINI
            r_ctog = r_itog @ R_CTOI
            stamps.append(t)
            poses.append((r_ctog, p_cing))
    return stamps, poses


def nearest_pose(stamps, poses, t, max_dt):
    idx = bisect_left(stamps, t)
    candidates = []
    if idx < len(stamps):
        candidates.append(idx)
    if idx > 0:
        candidates.append(idx - 1)
    if not candidates:
        return None
    best = min(candidates, key=lambda i: abs(stamps[i] - t))
    if abs(stamps[best] - t) > max_dt:
        return None
    return poses[best]


def projection_from_pose(r_ctog, p_cing):
    r_gtoc = r_ctog.T
    t_gtoc = -r_gtoc @ p_cing
    return np.hstack([r_gtoc, t_gtoc.reshape(3, 1)])


def project_pixels(points_g, r_ctog, p_cing):
    r_gtoc = r_ctog.T
    t_gtoc = -r_gtoc @ p_cing
    rvec, _ = cv2.Rodrigues(r_gtoc)
    img_pts, _ = cv2.fisheye.projectPoints(
        points_g.reshape(-1, 1, 3).astype(np.float64),
        rvec,
        t_gtoc.reshape(3, 1),
        K,
        D,
    )
    return img_pts.reshape(-1, 2)


def undistort_norm(points):
    pts = points.reshape(-1, 1, 2).astype(np.float64)
    return cv2.fisheye.undistortPoints(pts, K, D).reshape(-1, 2)


def write_ply(path, points, colors):
    with path.open("w") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(points)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("end_header\n")
        for p, c in zip(points, colors):
            f.write(
                f"{p[0]:.6f} {p[1]:.6f} {p[2]:.6f} "
                f"{int(c[2])} {int(c[1])} {int(c[0])}\n"
            )


def voxel_downsample(points, colors, voxel):
    if len(points) == 0:
        return points, colors
    buckets = {}
    for p, c in zip(points, colors):
        key = tuple(np.floor(p / voxel).astype(np.int64))
        if key not in buckets:
            buckets[key] = [p.copy(), c.astype(np.float64), 1]
        else:
            buckets[key][0] += p
            buckets[key][1] += c
            buckets[key][2] += 1
    out_p, out_c = [], []
    for p_sum, c_sum, n in buckets.values():
        out_p.append(p_sum / n)
        out_c.append(np.clip(c_sum / n, 0, 255).astype(np.uint8))
    return np.asarray(out_p), np.asarray(out_c)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--traj", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--step", type=int, default=12)
    parser.add_argument("--max-dt", type=float, default=0.06)
    parser.add_argument("--min-baseline", type=float, default=0.025)
    parser.add_argument("--max-depth", type=float, default=30.0)
    parser.add_argument("--max-reproj-px", type=float, default=4.0)
    parser.add_argument("--voxel", type=float, default=0.03)
    args = parser.parse_args()

    video_path = args.session / "raw_video.mp4"
    timestamps = read_video_timestamps(args.session / "video_timestamps.csv")
    traj_stamps, poses = read_traj(args.traj)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {video_path}")

    points_all, colors_all = [], []
    prev = None
    selected = []
    for frame_idx in range(0, len(timestamps), args.step):
        pose = nearest_pose(traj_stamps, poses, timestamps[frame_idx], args.max_dt)
        if pose is not None:
            selected.append((frame_idx, timestamps[frame_idx], pose))

    for a, b in zip(selected[:-1], selected[1:]):
        idx0, _, pose0 = a
        idx1, _, pose1 = b
        baseline = np.linalg.norm(pose1[1] - pose0[1])
        if baseline < args.min_baseline:
            continue

        cap.set(cv2.CAP_PROP_POS_FRAMES, idx0)
        ok0, img0 = cap.read()
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx1)
        ok1, img1 = cap.read()
        if not ok0 or not ok1:
            continue

        g0 = cv2.cvtColor(img0, cv2.COLOR_BGR2GRAY)
        g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        pts0 = cv2.goodFeaturesToTrack(
            g0,
            maxCorners=1200,
            qualityLevel=0.01,
            minDistance=10,
            blockSize=7,
        )
        if pts0 is None or len(pts0) < 30:
            continue
        pts1, status, _ = cv2.calcOpticalFlowPyrLK(
            g0,
            g1,
            pts0,
            None,
            winSize=(31, 31),
            maxLevel=4,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )
        status = status.reshape(-1).astype(bool)
        p0 = pts0.reshape(-1, 2)[status]
        p1 = pts1.reshape(-1, 2)[status]
        if len(p0) < 20:
            continue

        n0 = undistort_norm(p0)
        n1 = undistort_norm(p1)
        P0 = projection_from_pose(*pose0)
        P1 = projection_from_pose(*pose1)
        pts4 = cv2.triangulatePoints(P0, P1, n0.T, n1.T).T
        pts3 = pts4[:, :3] / pts4[:, 3:4]

        r0, c0 = pose0
        r1, c1 = pose1
        d0 = (r0.T @ (pts3 - c0).T).T[:, 2]
        d1 = (r1.T @ (pts3 - c1).T).T[:, 2]
        finite = np.isfinite(pts3).all(axis=1)
        good = finite & (d0 > 0.1) & (d1 > 0.1) & (d0 < args.max_depth) & (d1 < args.max_depth)
        if np.any(good):
            proj0 = project_pixels(pts3, *pose0)
            proj1 = project_pixels(pts3, *pose1)
            err0 = np.linalg.norm(proj0 - p0, axis=1)
            err1 = np.linalg.norm(proj1 - p1, axis=1)
            good &= (err0 < args.max_reproj_px) & (err1 < args.max_reproj_px)
        if not np.any(good):
            continue

        pts3 = pts3[good]
        pix = np.round(p0[good]).astype(np.int32)
        pix[:, 0] = np.clip(pix[:, 0], 0, img0.shape[1] - 1)
        pix[:, 1] = np.clip(pix[:, 1], 0, img0.shape[0] - 1)
        cols = img0[pix[:, 1], pix[:, 0]]
        points_all.append(pts3)
        colors_all.append(cols)

    if points_all:
        points = np.vstack(points_all)
        colors = np.vstack(colors_all)
        points, colors = voxel_downsample(points, colors, args.voxel)
    else:
        points = np.zeros((0, 3), dtype=np.float64)
        colors = np.zeros((0, 3), dtype=np.uint8)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_ply(args.output, points, colors)
    xyz_path = args.output.with_suffix(".xyz")
    np.savetxt(xyz_path, points, fmt="%.6f")
    summary = args.output.with_suffix(".summary.txt")
    summary.write_text(
        f"selected_frames={len(selected)}\n"
        f"points={len(points)}\n"
        f"step={args.step}\n"
        f"trajectory={args.traj}\n"
    )
    print(summary)
    print(f"points={len(points)} selected_frames={len(selected)}")


if __name__ == "__main__":
    main()
