"""OpenCV 自带 Aloe 双目示例：StereoSGBM 计算视差，再换算为相对深度。

在仓库根目录运行（首次会从 OpenCV 官方仓库下载 aloeL.jpg / aloeR.jpg）：
    python3.9 lab0/code/stereo_depth.py --scale 0.5
"""

import argparse
import json
from pathlib import Path
from urllib.request import urlretrieve

import cv2 as cv
import numpy as np

SAMPLE_URL = "https://raw.githubusercontent.com/opencv/opencv/4.x/samples/data/"
DATA = Path("lab0/data/stereo")
OUTPUT = Path("lab0/results/stereo")
NUM_DISPARITIES = 128  # 视差搜索范围，须为 16 的倍数


def load_sample():
    """读取 Aloe 左右图；本地没有时先下载。这对图像已经做过立体校正。"""
    DATA.mkdir(parents=True, exist_ok=True)
    images = []
    for name in ("aloeL.jpg", "aloeR.jpg"):
        path = DATA / name
        if not path.exists():
            urlretrieve(SAMPLE_URL + name, path)
        images.append(cv.imread(str(path)))
    return images


def colour_map(values, valid, reverse=False):
    """仅用于作图：按有效值的 2%～98% 分位数拉伸后上色，无效像素涂黑。"""
    lo, hi = np.percentile(values[valid], [2, 98])
    scaled = np.clip((values[valid] - lo) / (hi - lo), 0, 1)
    if reverse:  # 深度图反转颜色，使近处和视差图一样呈暖色
        scaled = 1 - scaled
    gray = np.zeros(values.shape, np.uint8)
    gray[valid] = (scaled * 255).astype(np.uint8)
    result = cv.applyColorMap(gray, cv.COLORMAP_TURBO)
    result[~valid] = 0
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scale", type=float, default=0.5, help="图像缩放比例")
    parser.add_argument("--block-size", type=int, default=5, help="匹配窗口边长，奇数")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)

    left, right = load_sample()
    left = cv.resize(left, None, fx=args.scale, fy=args.scale, interpolation=cv.INTER_AREA)
    right = cv.resize(right, None, fx=args.scale, fy=args.scale, interpolation=cv.INTER_AREA)
    height, width = left.shape[:2]

    # 1. 检查图：左右图并排画水平线；已校正时，同一物点应落在同一条水平线上。
    pair = np.hstack((left, right))
    for y in range(40, height, height // 8):
        cv.line(pair, (0, y), (pair.shape[1] - 1, y), (0, 255, 0), 1)
    cv.imwrite(str(OUTPUT / "rectified_pair_check.png"), pair)

    # 2. SGBM 沿水平扫描线找对应点；P1、P2 惩罚相邻像素的视差跳变，使视差图更平滑。
    b = args.block_size
    matcher = cv.StereoSGBM_create(
        minDisparity=0, numDisparities=NUM_DISPARITIES, blockSize=b,
        P1=8 * b * b, P2=32 * b * b, disp12MaxDiff=1, uniquenessRatio=10,
        speckleWindowSize=100, speckleRange=2, mode=cv.STEREO_SGBM_MODE_SGBM_3WAY)
    raw = matcher.compute(cv.cvtColor(left, cv.COLOR_BGR2GRAY), cv.cvtColor(right, cv.COLOR_BGR2GRAY))
    disparity = raw.astype(np.float32) / 16.0  # OpenCV 以 1/16 像素为单位输出定点视差
    valid = disparity > 0  # 失败的匹配为负值；零视差对应无穷远，也不参与换算

    # 3. 视差 → 深度：已校正双目满足 Z = f·B / d。
    #    这对示例图没有给出标定参数，沿用 OpenCV 示例的假设 f = 0.8·宽度，并令基线 B = 1。
    #    因此结果只反映远近关系，单位是“基线长度”，不是米。
    focal, baseline = 0.8 * width, 1.0
    depth = np.full(disparity.shape, np.nan, np.float32)  # 无效像素记为 NaN，而不是 0
    depth[valid] = focal * baseline / disparity[valid]

    np.save(OUTPUT / "disparity_px.npy", disparity)
    np.save(OUTPUT / "depth_approx_baseline_units.npy", depth)
    cv.imwrite(str(OUTPUT / "disparity.png"), colour_map(disparity, valid))
    cv.imwrite(str(OUTPUT / "depth_preview.png"), colour_map(depth, valid, reverse=True))
    cv.imwrite(str(OUTPUT / "valid_mask.png"), valid.astype(np.uint8) * 255)
    summary = {
        "image_size_px": [width, height], "scale": args.scale,
        "num_disparities": NUM_DISPARITIES, "block_size": b,
        "valid_fraction": float(valid.mean()),
        "focal_px_assumed": focal, "baseline": baseline, "depth_unit": "baseline units (not metres)",
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("有效像素比例：{:.1%}；结果目录：{}".format(valid.mean(), OUTPUT))


if __name__ == "__main__":
    main()
