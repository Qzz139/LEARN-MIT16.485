# Lab0 程序使用说明

从仓库根目录运行。已在 **Python 3.9.23、NumPy 2.0.2、OpenCV 4.12.0** 下验证，无需图形界面。新环境先安装依赖：

```bash
python3.9 -m venv lab0/.venv
source lab0/.venv/bin/activate
python -m pip install -r lab0/requirements.txt
```

## Lab0-1：手机相机内参标定（`code/calibrate_phone.py`）

19 张手机原图在 `lab0/data/phone/`（HEIC），已用 `heif-convert` 转为 `lab0/data/phone_jpg/` 中的 JPG。照片体积大，不随仓库提供，只保存在本地；克隆后需放入自己的棋盘照片。HEIC 转 JPG：

```bash
mkdir -p lab0/data/phone_jpg
for file in lab0/data/phone/*.HEIC; do
  heif-convert --quiet -q 95 "$file" "lab0/data/phone_jpg/$(basename "$file" .HEIC).jpg"
done
```

运行标定：

```bash
python3.9 lab0/code/calibrate_phone.py --images lab0/data/phone_jpg --square-size-m 0.025
```

程序步骤：① 生成棋盘角点的世界坐标（Z=0 平面）；② 逐张检测 8×5 个内部角点（附件棋盘 9×6 个方格），经典检测器失败时改用 SB 检测器——本组照片中 `IMG_2307` 就是这种情况；③ `calibrateCamera` 求内参 K 与畸变；④ 自行重算逐图及全局重投影 RMS；⑤ 保存结果。棋盘显示在笔记本屏幕上，`0.025` 是屏幕上**实测**的单格边长，不是 PDF 标注的打印尺寸。棋盘规格写在程序顶部的 `PATTERN` 常量里。

输出在 `lab0/results/calibration/`：

| 文件 | 内容 |
| --- | --- |
| `summary.json` | K、畸变系数、全局及逐图重投影误差 |
| `calibration.npz` | K、畸变系数和图像尺寸，供其他程序读取 |
| `corners/*.png` | 标出角点的照片，供报告核对 |
| `before_after.png` | 第一张照片去畸变前后对比 |

`corners/` 和 `before_after.png` 体积大，只保存在本地；仓库只保留 `summary.json`、`calibration.npz` 和报告里用到的精选图（`lab0/reports/figures/`）。K 的焦距以像素计；方格边长只影响每张照片位姿的平移尺度，不影响 K。

## Lab0-2：OpenCV Aloe 双目深度（`code/stereo_depth.py`）

首次运行会从 OpenCV 官方仓库下载 `aloeL.jpg`、`aloeR.jpg` 到 `lab0/data/stereo/`，之后复用本地文件：

```bash
python3.9 lab0/code/stereo_depth.py --scale 0.5
```

程序步骤：① 左右图缩小一半，并排画水平线作对齐检查；② `StereoSGBM` 求视差，OpenCV 的定点输出除以 16 得到像素视差；③ 按 `Z = f·B / d` 换算深度。报告里还做了一次 `--block-size 9` 的对比运行（默认 5，须为奇数）。

示例图没有配套标定参数，程序沿用 OpenCV 示例的假设焦距 `f = 0.8 × 图像宽度`，基线取 `B = 1`。所以深度只反映远近关系，单位是“基线长度”，**不是米**。

输出在 `lab0/results/stereo/`：

| 文件 | 内容 |
| --- | --- |
| `rectified_pair_check.png` | 左右图并排和水平参考线 |
| `disparity_px.npy`、`disparity.png` | 像素视差及可视化 |
| `valid_mask.png` | 视差有效（d > 0）的像素 |
| `depth_approx_baseline_units.npy`、`depth_preview.png` | 相对深度及预览 |
| `summary.json` | 参数、有效像素比例和深度单位 |

## 报告与译稿

两篇[中文论文译稿](translation/)和两份[英文实验报告](reports/)按 [Lab0 要求](readme.md) 分开提交。报告插图由 `python3.9 lab0/reports/build_figures.py` 从上述输出生成。

参考：[OpenCV 相机标定教程](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html)、[OpenCV 官方 Aloe 双目示例](https://github.com/opencv/opencv/blob/4.x/samples/python/stereo_match.py)。
