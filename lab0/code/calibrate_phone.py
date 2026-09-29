"""用多张棋盘照片标定手机相机内参（张正友标定法的 OpenCV 实现）。

在仓库根目录运行：
    python3.9 lab0/code/calibrate_phone.py --images lab0/data/phone_jpg --square-size-m 0.025
"""

import argparse
import json
from pathlib import Path

import cv2 as cv
import numpy as np

PATTERN = (8, 5)  # 内部角点数（列, 行）：附件棋盘有 9×6 个方格，内部角点为 8×5
OUTPUT = Path("lab0/results/calibration")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, default=Path("lab0/data/phone_jpg"), help="棋盘照片目录")
    parser.add_argument("--square-size-m", type=float, default=0.025, help="实测方格边长，单位米")
    args = parser.parse_args()
    (OUTPUT / "corners").mkdir(parents=True, exist_ok=True)
    # 本机（Apple M3, OpenCV 4.12）上，只要开着 OpenCL 或多线程，下面的 SB 检测器就会崩溃
    # 或每次给出略有不同的角点；两者都关掉后结果稳定可复现。
    cv.ocl.setUseOpenCL(False)
    cv.setNumThreads(1)

    # 1. 棋盘角点的世界坐标：棋盘位于 Z=0 平面，第 (i, j) 个角点为 (i·s, j·s, 0)。
    grid = np.zeros((PATTERN[0] * PATTERN[1], 3), np.float32)
    grid[:, :2] = np.mgrid[0:PATTERN[0], 0:PATTERN[1]].T.reshape(-1, 2)
    grid *= args.square_size_m

    # 2. 逐张检测角点，得到“世界点 ↔ 像素点”的对应关系。
    paths = sorted(p for p in args.images.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    object_points, image_points, used = [], [], []
    for path in paths:
        image = cv.imread(str(path))
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        found, corners = cv.findChessboardCorners(gray, PATTERN)
        if found:
            # 经典检测器给出整像素角点，再细化到亚像素精度。
            criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        else:
            # 本组照片中 IMG_2307 只能由 SB 检测器找到；SB 的输出本身已是亚像素精度。
            found, corners = cv.findChessboardCornersSB(gray, PATTERN)
        if not found:
            print("跳过（未检测到全部角点）：", path.name)
            continue
        object_points.append(grid)
        image_points.append(corners)
        used.append(path)
        cv.drawChessboardCorners(image, PATTERN, corners, True)
        cv.imwrite(str(OUTPUT / "corners" / "{:03d}.png".format(len(used))), image)

    # 3. 联合所有视角，求内参 K、畸变系数和每张照片的位姿 (R, t)。
    image_size = (gray.shape[1], gray.shape[0])
    rms, K, dist, rvecs, tvecs = cv.calibrateCamera(object_points, image_points, image_size, None, None)

    # 4. 重投影误差：用标定结果把棋盘点投影回图像，与检测到的角点比较。
    per_view, total_sq, total_n = [], 0.0, 0
    for path, obj, observed, rvec, tvec in zip(used, object_points, image_points, rvecs, tvecs):
        predicted, _ = cv.projectPoints(obj, rvec, tvec, K, dist)
        sq = float(np.sum((observed.reshape(-1, 2) - predicted.reshape(-1, 2)) ** 2))
        total_sq += sq
        total_n += len(obj)
        per_view.append({"file": path.name, "rms_px": float(np.sqrt(sq / len(obj)))})
    # 全局 RMS 要把所有角点放在一起算，不能直接平均各图的 RMS。
    rms_check = float(np.sqrt(total_sq / total_n))

    # 5. 保存结果：去畸变对比图、数值参数和报告用的摘要。
    first = cv.imread(str(used[0]))
    cv.imwrite(str(OUTPUT / "before_after.png"), np.hstack((first, cv.undistort(first, K, dist))))
    np.savez(OUTPUT / "calibration.npz", camera_matrix=K, distortion=dist, image_size=np.array(image_size))
    summary = {
        "camera_matrix": K.tolist(),
        "distortion": dist.ravel().tolist(),
        "image_size_px": list(image_size),
        "checkerboard_inner_corners": list(PATTERN),
        "square_size_m": args.square_size_m,
        "opencv_rms_px": float(rms),
        "recomputed_rms_px": rms_check,
        "used_count": len(used),
        "per_view": per_view,
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("有效照片：{}/{}；重投影 RMS：{:.3f} px".format(len(used), len(paths), rms_check))
    print("内参 K：\n{}\n畸变系数：{}".format(K, dist.ravel()))


if __name__ == "__main__":
    main()
