"""从不同角度拍摄的棋盘照片中标定手机相机。"""

import argparse
import json
from pathlib import Path

import cv2 as cv
import numpy as np


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def read_image(path):
    # 用字节流解码，兼容包含中文字符的文件路径。
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv.imdecode(data, cv.IMREAD_COLOR)


def write_image(path, image):
    # 与 read_image 对应：先编码，再写入可能含中文的路径。
    ok, encoded = cv.imencode(path.suffix, image)
    if not ok:
        raise RuntimeError("无法编码图像：{}".format(path))
    encoded.tofile(str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, required=True, help="手机拍摄的棋盘照片目录")
    parser.add_argument("--output", type=Path, default=Path("lab0/results/calibration"))
    parser.add_argument("--columns", type=int, default=8, help="水平方向的内部角点数")
    parser.add_argument("--rows", type=int, default=5, help="竖直方向的内部角点数")
    parser.add_argument("--square-size-m", type=float, default=0.025, help="实测方格边长，单位米")
    parser.add_argument("--min-views", type=int, default=10)
    args = parser.parse_args()

    if args.columns < 2 or args.rows < 2 or args.square_size_m <= 0 or args.min_views < 3:
        parser.error("角点数须不小于 2，方格边长须为正，最少视角数须不小于 3")
    if not args.images.is_dir():
        parser.error("照片目录不存在：{}".format(args.images))

    paths = sorted(p for p in args.images.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
    if not paths:
        parser.error("照片目录中没有 JPG、PNG、BMP 或 TIFF 图像")

    args.output.mkdir(parents=True, exist_ok=True)
    corner_dir = args.output / "corners"
    corner_dir.mkdir(exist_ok=True)
    # 附件为 9×6 个方格，OpenCV 需要的是 8×5 个“内部角点”。
    pattern = (args.columns, args.rows)
    # 将棋盘置于 Z=0 平面；方格边长决定物点坐标的米制尺度。
    object_grid = np.zeros((args.columns * args.rows, 3), np.float32)
    object_grid[:, :2] = np.mgrid[0:args.columns, 0:args.rows].T.reshape(-1, 2)
    object_grid *= args.square_size_m
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    object_points, image_points, used, rejected = [], [], [], []
    image_size = None
    for path in paths:
        image = read_image(path)
        if image is None:
            rejected.append({"file": path.name, "reason": "无法解码"})
            continue
        size = (image.shape[1], image.shape[0])
        # 同一次标定要使用一致的像素坐标系，因此排除不同分辨率的照片。
        if image_size is None:
            image_size = size
        if size != image_size:
            rejected.append({"file": path.name, "reason": "分辨率与其他照片不一致"})
            continue
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        found, corners = cv.findChessboardCorners(gray, pattern)
        if found:
            # 经典检测器返回的角点再细化到亚像素精度。
            corners = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        elif hasattr(cv, "findChessboardCornersSB"):
            # SB 检测器可补救部分困难视角，输出本身已有亚像素精度。
            found, corners = cv.findChessboardCornersSB(gray, pattern)
        if not found:
            rejected.append({"file": path.name, "reason": "未检测到全部内部角点"})
            continue

        # 物点和像点按相同角点顺序成对保存，供标定与复查使用。
        object_points.append(object_grid.copy())
        image_points.append(corners)
        used.append(path)
        cv.drawChessboardCorners(image, pattern, corners, True)
        write_image(corner_dir / ("{:03d}.png".format(len(used))), image)

    if len(used) < args.min_views:
        raise RuntimeError("只检测成功 {}/{} 张；至少需要 {} 张有效照片。失败详情：{}".format(
            len(used), len(paths), args.min_views, rejected))

    # 联合各视角求内参 K、畸变，以及每张照片各自的旋转/平移。
    rms, camera_matrix, distortion, rvecs, tvecs = cv.calibrateCamera(
        object_points, image_points, image_size, None, None)
    view_errors = []
    total_squared_error = 0.0
    total_points = 0
    for path, obj, observed, rvec, tvec in zip(used, object_points, image_points, rvecs, tvecs):
        # 把已知棋盘点投影回照片，比较预测角点与实际检测角点。
        predicted, _ = cv.projectPoints(obj, rvec, tvec, camera_matrix, distortion)
        differences = observed.reshape(-1, 2) - predicted.reshape(-1, 2)
        squared_error = float(np.sum(differences ** 2))
        total_squared_error += squared_error
        total_points += len(obj)
        # 每张图 RMS = sqrt(该图所有角点的二维像素误差平方和 / 角点数)。
        view_errors.append({"file": path.name, "rms_px": float(np.sqrt(squared_error / len(obj)))})

    # 全局 RMS 按全部角点一起计算，不能直接平均各图的 RMS。
    check_rms = float(np.sqrt(total_squared_error / total_points))
    first = read_image(used[0])
    corrected = cv.undistort(first, camera_matrix, distortion)
    write_image(args.output / "before_after.png", np.hstack((first, corrected)))
    # 数值数据供程序复用，JSON 与图像可直接用于实验报告。
    np.savez_compressed(args.output / "calibration.npz", camera_matrix=camera_matrix,
                        distortion=distortion, image_size=np.array(image_size),
                        square_size_m=args.square_size_m,
                        rvecs=np.asarray(rvecs), tvecs=np.asarray(tvecs),
                        view_files=np.asarray([path.name for path in used]))
    summary = {
        "camera_matrix": camera_matrix.tolist(),
        "distortion": distortion.reshape(-1).tolist(),
        "image_size_px": list(image_size),
        "checkerboard_inner_corners": list(pattern),
        "square_size_m": args.square_size_m,
        "opencv_rms_px": float(rms),
        "recomputed_rms_px": check_rms,
        "used_count": len(used),
        "rejected": rejected,
        "per_view": view_errors,
    }
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("有效照片：{}/{}；全局重投影 RMS：{:.3f} px".format(len(used), len(paths), check_rms))
    print("相机内参 K：\n{}".format(camera_matrix))
    print("畸变系数：{}".format(distortion.reshape(-1)))
    print("结果目录：{}".format(args.output.resolve()))


if __name__ == "__main__":
    main()
