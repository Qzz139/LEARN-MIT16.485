"""Compute disparity and depth from an already rectified stereo image pair."""

import argparse
import json
from pathlib import Path
from urllib.request import urlopen

import cv2 as cv
import numpy as np


SAMPLE_BASE = "https://raw.githubusercontent.com/opencv/opencv/4.x/samples/data/"


def read_image(path):
    return cv.imdecode(np.fromfile(str(path), dtype=np.uint8), cv.IMREAD_COLOR)


def write_image(path, image):
    ok, encoded = cv.imencode(path.suffix, image)
    if not ok:
        raise RuntimeError("无法编码图像：{}".format(path))
    encoded.tofile(str(path))


def sample_images(directory):
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in ("aloeL.jpg", "aloeR.jpg"):
        path = directory / name
        if not path.exists():
            with urlopen(SAMPLE_BASE + name, timeout=30) as response:
                path.write_bytes(response.read())
        paths.append(path)
    return paths


def colour_map(values, valid, reverse=False):
    result = np.zeros((*values.shape, 3), dtype=np.uint8)
    if not np.any(valid):
        return result
    lo, hi = np.percentile(values[valid], [2, 98])
    if hi <= lo:
        hi = lo + 1.0
    scaled = np.clip((values[valid] - lo) / (hi - lo), 0, 1)
    if reverse:
        scaled = 1 - scaled
    gray = np.zeros(values.shape, dtype=np.uint8)
    gray[valid] = (scaled * 255).astype(np.uint8)
    result = cv.applyColorMap(gray, cv.COLORMAP_TURBO)
    result[~valid] = 0
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sample", action="store_true", help="下载并使用 OpenCV Aloe 双目示例")
    source.add_argument("--left", type=Path, help="已经校正的左图；需同时提供 --right")
    parser.add_argument("--right", type=Path, help="已经校正的右图")
    parser.add_argument("--sample-dir", type=Path, default=Path("lab0/data/stereo"))
    parser.add_argument("--output", type=Path, default=Path("lab0/results/stereo"))
    parser.add_argument("--scale", type=float, default=1.0, help="图像缩放比例，焦距也必须使用缩放后的像素值")
    parser.add_argument("--min-disparity", type=int, default=0)
    parser.add_argument("--num-disparities", type=int, default=128, help="正整数，且须为 16 的倍数")
    parser.add_argument("--block-size", type=int, default=5, help="奇数，至少为 3")
    parser.add_argument("--focal-px", type=float, help="校正后、在当前图像尺寸下的真实焦距，单位像素")
    parser.add_argument("--baseline-m", type=float, help="双目真实基线，单位米")
    parser.add_argument("--cx-difference-px", type=float, default=0.0,
                        help="校正后左主点横坐标减右主点横坐标，单位像素")
    args = parser.parse_args()

    if args.sample and args.right:
        parser.error("使用 --sample 时不需要 --right")
    if args.left and not args.right:
        parser.error("使用 --left 时必须提供 --right")
    if (args.focal_px is None) != (args.baseline_m is None):
        parser.error("真实尺度深度需要同时提供 --focal-px 和 --baseline-m")
    if args.focal_px is not None and (args.focal_px <= 0 or args.baseline_m <= 0):
        parser.error("焦距和基线必须为正")
    if not 0 < args.scale <= 1:
        parser.error("--scale 必须在 (0, 1] 范围内")
    if args.num_disparities <= 0 or args.num_disparities % 16 != 0:
        parser.error("--num-disparities 必须是正的 16 的倍数")
    if args.block_size < 3 or args.block_size % 2 != 1:
        parser.error("--block-size 必须是不小于 3 的奇数")

    left_path, right_path = sample_images(args.sample_dir) if args.sample else (args.left, args.right)
    left, right = read_image(left_path), read_image(right_path)
    if left is None or right is None:
        raise RuntimeError("无法读取双目图像；检查文件是否存在且格式受 OpenCV 支持")
    if left.shape != right.shape:
        raise RuntimeError("左右图像分辨率必须一致")
    if args.scale != 1:
        left = cv.resize(left, None, fx=args.scale, fy=args.scale, interpolation=cv.INTER_AREA)
        right = cv.resize(right, None, fx=args.scale, fy=args.scale, interpolation=cv.INTER_AREA)

    height, width = left.shape[:2]
    if width <= args.num_disparities + max(args.min_disparity, 0):
        parser.error("图像宽度不足以使用当前的视差搜索范围")
    matcher = cv.StereoSGBM_create(
        minDisparity=args.min_disparity,
        numDisparities=args.num_disparities,
        blockSize=args.block_size,
        P1=8 * args.block_size ** 2,
        P2=32 * args.block_size ** 2,
        disp12MaxDiff=1,
        uniquenessRatio=10,
        speckleWindowSize=100,
        speckleRange=2,
        mode=cv.STEREO_SGBM_MODE_SGBM_3WAY,
    )
    gray_left = cv.cvtColor(left, cv.COLOR_BGR2GRAY)
    gray_right = cv.cvtColor(right, cv.COLOR_BGR2GRAY)
    disparity = matcher.compute(gray_left, gray_right).astype(np.float32) / 16.0
    valid = np.isfinite(disparity) & (disparity > args.min_disparity) & (disparity > 0)
    args.output.mkdir(parents=True, exist_ok=True)
    np.save(args.output / "disparity_px.npy", disparity)
    write_image(args.output / "disparity.png", colour_map(disparity, valid))

    pair = np.hstack((left, right))
    for y in range(40, height, max(height // 8, 1)):
        cv.line(pair, (0, y), (pair.shape[1] - 1, y), (0, 255, 0), 1)
    write_image(args.output / "rectified_pair_check.png", pair)

    summary = {
        "left": str(left_path), "right": str(right_path), "image_size_px": [width, height],
        "assumed_rectified": True, "scale": args.scale,
        "min_disparity": args.min_disparity, "num_disparities": args.num_disparities,
        "block_size": args.block_size, "valid_fraction": float(valid.mean()),
        "cx_difference_px": args.cx_difference_px,
        "opencv_version": cv.__version__,
    }
    if args.focal_px is None:
        # The official Aloe example guesses f = 0.8 * image width. B=1 is an
        # arbitrary baseline unit, so these values are illustrative only.
        focal = 0.8 * width
        baseline = 1.0
        filename = "depth_approx_baseline_units.npy"
        summary.update({"depth_unit": "arbitrary baseline unit", "metric_depth": False,
                        "focal_px": focal, "baseline": baseline,
                        "warning": "焦距是 OpenCV Aloe 示例的估计值；深度没有真实米制尺度"})
    else:
        focal = args.focal_px
        baseline = args.baseline_m
        filename = "depth_m.npy"
        summary.update({"depth_unit": "m", "metric_depth": True,
                        "focal_px": focal, "baseline_m": baseline})

    denominator = disparity - args.cx_difference_px
    valid &= denominator > 0
    write_image(args.output / "valid_mask.png", (valid * 255).astype(np.uint8))
    depth = np.full(disparity.shape, np.nan, dtype=np.float32)
    depth[valid] = (focal * baseline / denominator[valid]).astype(np.float32)
    np.save(args.output / filename, depth)
    write_image(args.output / "depth_preview.png", colour_map(depth, valid, reverse=True))
    summary["valid_fraction"] = float(valid.mean())
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if not np.any(valid):
        print("警告：没有有效视差。请检查左右图顺序、校正情况和视差搜索范围。")
    print("有效像素比例：{:.1%}".format(valid.mean()))
    print("深度单位：{}；结果目录：{}".format(summary["depth_unit"], args.output.resolve()))


if __name__ == "__main__":
    main()
