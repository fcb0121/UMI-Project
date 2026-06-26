#!/usr/bin/env python3
"""Plane-stabilize a visual SLAM trajectory for inspection.

This is a post-processing diagnostic tool. It does not fix the SLAM backend;
it estimates the dominant motion plane from valid camera centers, projects the
trajectory onto that plane, and writes CloudCompare-friendly files.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Iterable

import numpy as np


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def read_trajectory(path: Path) -> tuple[list[dict[str, str]], np.ndarray, np.ndarray]:
    rows: list[dict[str, str]] = []
    valid_indices: list[int] = []
    positions: list[list[float]] = []

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            rows.append(row)
            pos = np.array([float(row["x"]), float(row["y"]), float(row["z"])], dtype=float)
            quat = np.array(
                [float(row["q_x"]), float(row["q_y"]), float(row["q_z"]), float(row["q_w"])],
                dtype=float,
            )
            if parse_bool(row["is_lost"]):
                continue
            if not np.isfinite(pos).all() or not np.isfinite(quat).all():
                continue
            if np.linalg.norm(quat) < 1e-9:
                continue
            valid_indices.append(i)
            positions.append(pos.tolist())

    if len(positions) < 3:
        raise ValueError(f"Need at least 3 valid trajectory points in {path}")

    return rows, np.asarray(valid_indices, dtype=int), np.asarray(positions, dtype=float)


def robust_plane_pca(points: np.ndarray, rounds: int = 4) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mask = np.ones(points.shape[0], dtype=bool)
    for _ in range(rounds):
        pts = points[mask]
        center = np.median(pts, axis=0)
        centered = pts - center
        _, _, vh = np.linalg.svd(centered, full_matrices=False)
        normal = vh[-1]
        residuals = np.abs((points - center) @ normal)
        med = np.median(residuals[mask])
        mad = np.median(np.abs(residuals[mask] - med))
        sigma = 1.4826 * mad if mad > 1e-12 else np.std(residuals[mask])
        if sigma <= 1e-12:
            break
        new_mask = residuals <= med + 3.5 * sigma
        if new_mask.sum() < max(3, points.shape[0] // 3):
            break
        if np.array_equal(new_mask, mask):
            break
        mask = new_mask

    pts = points[mask]
    center = np.median(pts, axis=0)
    centered = pts - center
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    axes = vh.copy()
    if np.linalg.det(axes) < 0:
        axes[-1] *= -1
    return center, axes, mask


def transform_points(points: np.ndarray, center: np.ndarray, axes: np.ndarray) -> np.ndarray:
    return (points - center) @ axes.T


def read_ascii_ply_xyz(path: Path) -> np.ndarray:
    with path.open() as f:
        header: list[str] = []
        vertex_count = None
        for line in f:
            header.append(line.rstrip("\n"))
            if line.startswith("element vertex"):
                vertex_count = int(line.split()[2])
            if line.strip() == "end_header":
                break
        if vertex_count is None:
            raise ValueError(f"No vertex count in {path}")
        pts = []
        for _ in range(vertex_count):
            parts = f.readline().split()
            if len(parts) < 3:
                break
            pts.append([float(parts[0]), float(parts[1]), float(parts[2])])
    return np.asarray(pts, dtype=float)


def color_ramp(t: float) -> tuple[int, int, int]:
    t = min(1.0, max(0.0, t))
    stops = [
        (0.0, (0, 80, 255)),
        (0.25, (0, 220, 255)),
        (0.50, (0, 220, 60)),
        (0.75, (255, 220, 0)),
        (1.0, (255, 40, 0)),
    ]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= t <= b:
            u = (t - a) / (b - a)
            return tuple(int(round(ca[i] * (1.0 - u) + cb[i] * u)) for i in range(3))
    return stops[-1][1]


def write_ply(path: Path, vertices: Iterable[tuple[float, float, float, int, int, int]]) -> None:
    verts = list(vertices)
    with path.open("w") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(verts)}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("end_header\n")
        for x, y, z, r, g, b in verts:
            f.write(f"{x:.9f} {y:.9f} {z:.9f} {r:d} {g:d} {b:d}\n")


def write_obj_polyline(path: Path, points: np.ndarray) -> None:
    with path.open("w") as f:
        f.write("# plane-stabilized trajectory polyline\n")
        for p in points:
            f.write(f"v {p[0]:.9f} {p[1]:.9f} {p[2]:.9f}\n")
        for i in range(1, len(points)):
            f.write(f"l {i} {i + 1}\n")


def write_csv(path: Path, rows: list[dict[str, str]], valid_indices: np.ndarray, flat: np.ndarray, raw: np.ndarray) -> None:
    by_index = {int(idx): (flat[j], raw[j, 2]) for j, idx in enumerate(valid_indices)}
    fields = [
        "frame_idx",
        "timestamp",
        "x_plane",
        "y_plane",
        "z_plane",
        "raw_normal_offset",
        "is_keyframe",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(rows):
            if i not in by_index:
                continue
            p, z_raw = by_index[i]
            writer.writerow(
                {
                    "frame_idx": row["frame_idx"],
                    "timestamp": row["timestamp"],
                    "x_plane": f"{p[0]:.9f}",
                    "y_plane": f"{p[1]:.9f}",
                    "z_plane": f"{p[2]:.9f}",
                    "raw_normal_offset": f"{z_raw:.9f}",
                    "is_keyframe": row["is_keyframe"],
                }
            )


def write_svg(path: Path, points: np.ndarray, title: str) -> None:
    xy = points[:, :2]
    mn = xy.min(axis=0)
    mx = xy.max(axis=0)
    span = np.maximum(mx - mn, 1e-6)
    width, height, pad = 1200, 900, 50
    scale = min((width - 2 * pad) / span[0], (height - 2 * pad) / span[1])

    def project(p: np.ndarray) -> tuple[float, float]:
        x = pad + (p[0] - mn[0]) * scale
        y = height - pad - (p[1] - mn[1]) * scale
        return x, y

    with path.open("w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n')
        f.write('<rect width="100%" height="100%" fill="white"/>\n')
        f.write(f'<text x="{pad}" y="32" font-family="monospace" font-size="20">{title}</text>\n')
        for i in range(1, len(points)):
            x1, y1 = project(points[i - 1])
            x2, y2 = project(points[i])
            r, g, b = color_ramp(i / max(1, len(points) - 1))
            f.write(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="rgb({r},{g},{b})" stroke-width="2"/>\n')
        for i, p in enumerate(points):
            x, y = project(p)
            r, g, b = color_ramp(i / max(1, len(points) - 1))
            f.write(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.2" fill="rgb({r},{g},{b})"/>\n')
        f.write("</svg>\n")


def path_stats(points: np.ndarray, raw_aligned: np.ndarray) -> dict[str, float]:
    steps = np.linalg.norm(np.diff(points[:, :3], axis=0), axis=1)
    xy = points[:, :2]
    xy_span = xy.max(axis=0) - xy.min(axis=0)
    z = raw_aligned[:, 2]
    return {
        "poses": float(points.shape[0]),
        "xy_range_x": float(xy_span[0]),
        "xy_range_y": float(xy_span[1]),
        "raw_normal_range": float(z.max() - z.min()),
        "raw_normal_rms": float(np.sqrt(np.mean((z - np.mean(z)) ** 2))),
        "path_length_flat": float(steps.sum()),
        "closure_distance_flat": float(np.linalg.norm(points[-1, :2] - points[0, :2])),
        "median_step_flat": float(np.median(steps)) if len(steps) else 0.0,
    }


def write_report(path: Path, source_traj: Path, source_map: Path, stats: dict[str, float], plane_mask_count: int) -> None:
    closure_ratio = stats["closure_distance_flat"] / max(stats["path_length_flat"], 1e-12)
    with path.open("w") as f:
        f.write("# Plane-stabilized visual trajectory\n\n")
        f.write("This is a diagnostic post-process. It projects valid camera centers onto the dominant motion plane estimated from the visual trajectory.\n\n")
        f.write(f"- source trajectory: `{source_traj}`\n")
        f.write(f"- source map: `{source_map}`\n")
        f.write(f"- valid poses: {int(stats['poses'])}\n")
        f.write(f"- poses used for robust plane fit: {plane_mask_count}\n")
        f.write(f"- flat XY range: {stats['xy_range_x']:.6f}, {stats['xy_range_y']:.6f}\n")
        f.write(f"- raw normal-axis range before flattening: {stats['raw_normal_range']:.6f}\n")
        f.write(f"- raw normal-axis RMS before flattening: {stats['raw_normal_rms']:.6f}\n")
        f.write(f"- flat path length: {stats['path_length_flat']:.6f}\n")
        f.write(f"- flat closure distance: {stats['closure_distance_flat']:.6f}\n")
        f.write(f"- closure/path ratio: {closure_ratio:.6f}\n")
        f.write(f"- median flat step: {stats['median_step_flat']:.6f}\n\n")
        f.write("Interpretation:\n\n")
        f.write("- If the flattened path is still not loop-like, the visual pose estimate is unstable in the table plane too.\n")
        f.write("- If the flattened path becomes loop-like, the visible tube was mostly normal-axis drift from monocular/PnP backend instability.\n")
        f.write("- The gray map points are not flattened; they are only transformed into the same plane-aligned coordinates.\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectory", required=True, type=Path)
    parser.add_argument("--mappoints", required=True, type=Path)
    parser.add_argument("--out-prefix", required=True, type=Path)
    args = parser.parse_args()

    rows, valid_indices, positions = read_trajectory(args.trajectory)
    center, axes, mask = robust_plane_pca(positions)
    traj_aligned = transform_points(positions, center, axes)
    traj_flat = traj_aligned.copy()
    traj_flat[:, 2] = 0.0

    map_points = read_ascii_ply_xyz(args.mappoints)
    map_aligned = transform_points(map_points, center, axes)

    traj_vertices = []
    for i, p in enumerate(traj_flat):
        r, g, b = color_ramp(i / max(1, len(traj_flat) - 1))
        traj_vertices.append((p[0], p[1], p[2], r, g, b))

    combined_vertices = [(p[0], p[1], p[2], 210, 210, 210) for p in map_aligned]
    combined_vertices.extend(traj_vertices)

    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)
    write_ply(args.out_prefix.with_name(args.out_prefix.name + "_trajectory_flat_color.ply"), traj_vertices)
    write_ply(args.out_prefix.with_name(args.out_prefix.name + "_map_plus_trajectory_flat.ply"), combined_vertices)
    write_obj_polyline(args.out_prefix.with_name(args.out_prefix.name + "_trajectory_flat_polyline.obj"), traj_flat)
    write_csv(args.out_prefix.with_name(args.out_prefix.name + "_trajectory_flat.csv"), rows, valid_indices, traj_flat, traj_aligned)
    write_svg(args.out_prefix.with_name(args.out_prefix.name + "_trajectory_flat_xy.svg"), traj_flat, args.out_prefix.name)
    stats = path_stats(traj_flat, traj_aligned)
    write_report(
        args.out_prefix.with_name(args.out_prefix.name + "_plane_stabilization_report.md"),
        args.trajectory,
        args.mappoints,
        stats,
        int(mask.sum()),
    )

    print(f"Wrote plane-stabilized outputs with prefix: {args.out_prefix}")
    print(f"valid poses: {int(stats['poses'])}, raw normal range: {stats['raw_normal_range']:.6f}")
    print(f"flat XY range: {stats['xy_range_x']:.6f}, {stats['xy_range_y']:.6f}")
    print(f"closure/path ratio: {stats['closure_distance_flat'] / max(stats['path_length_flat'], 1e-12):.6f}")


if __name__ == "__main__":
    main()
