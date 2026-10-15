# Lab 0 手操复现说明

环境：Mac（或任意装有 Python 3.9 的机器），不需要图形界面，命令都从仓库根目录运行。参照值来自已提交的结果；程序的详细参数和输出说明见 [PROGRAMS.md](PROGRAMS.md)，原理与实施建议见 [PLAN.md](PLAN.md)。

| 给分点 | 节 | 交付物与证据 |
| --- | --- | --- |
| Lab0-1 任务 1：翻译张正友论文（2） | §3 | [zhang1999_zh.pdf](translation/zhang1999_zh.pdf) |
| Lab0-1 任务 2：手机相机内参标定（3） | §1 | [calibration/summary.json](results/calibration/summary.json)、[报告](reports/lab0_1_camera_calibration.pdf) |
| Lab0-2 任务 1：翻译双目校正论文（2） | §3 | [fusiello2000_zh.pdf](translation/fusiello2000_zh.pdf) |
| Lab0-2 任务 2：双目深度估计（3） | §2 | [stereo/summary.json](results/stereo/summary.json)、[报告](reports/lab0_2_stereo_depth.pdf) |

## 0. 环境

```bash
python3.9 -m venv lab0/.venv && source lab0/.venv/bin/activate
python -m pip install -r lab0/requirements.txt
```

已验证的版本是 Python 3.9.23、NumPy 2.0.2、OpenCV 4.12.0。

## 1. 手机相机标定

棋盘照片体积大，不随仓库提供，只保存在本地。克隆仓库后，把自己拍的棋盘照片放进 `lab0/data/phone/`。iPhone 拍的 HEIC 格式先转成 JPG：

```bash
mkdir -p lab0/data/phone_jpg
for f in lab0/data/phone/*.HEIC; do heif-convert --quiet -q 95 "$f" "lab0/data/phone_jpg/$(basename "$f" .HEIC).jpg"; done
python3.9 lab0/code/calibrate_phone.py --images lab0/data/phone_jpg --square-size-m 0.025
```

**参数说明**：

- 棋盘是附件的 9×6 方格，内部角点 8×5；
- `0.025` 是在笔记本屏幕上**实测**的单格边长，不是 PDF 标注的打印尺寸。

**参照值**（[summary.json](results/calibration/summary.json)）：

| 指标 | 参照值 |
| --- | --- |
| 有效照片 | 19 张，4032×3024 |
| 重投影 RMS | 0.94 px |
| fx、fy | 2859.8、2856.4 px |
| 主点 (cx, cy) | (2014.6, 1523.8) |

输出在 `lab0/results/calibration/`：角点图 `corners/*.png`、去畸变对比图 `before_after.png`（这两项体积大，不提交）。

## 2. 双目深度估计（OpenCV Aloe 示例图）

```bash
python3.9 lab0/code/stereo_depth.py --scale 0.5
python3.9 lab0/code/stereo_depth.py --scale 0.5 --block-size 9
```

第一次运行会自动下载 `aloeL.jpg`、`aloeR.jpg`。第二条是报告里用来对比的另一组匹配窗口参数。

**参照值**（[summary.json](results/stereo/summary.json)）：

| 指标 | 参照值 |
| --- | --- |
| 图像尺寸 | 641×555（原图缩小一半） |
| 有效视差像素 | 70.5% |
| 焦距 | 假设为 512.8 px |

示例图没有配套的标定参数，所以深度的单位是"基线长度"，**不是米**。输出在 `lab0/results/stereo/`：对齐检查图、视差图、有效掩码、相对深度图。

## 3. 译稿与报告

两份译稿在 [translation](translation/)，两份英文报告在 [reports](reports/)，都已有 PDF。修改后重新生成的命令：

```bash
python3.9 lab0/reports/build_figures.py
cd lab0/reports && latexmk -xelatex lab0_1_camera_calibration.tex lab0_2_stereo_depth.tex && cd -
cd lab0/translation && latexmk -xelatex zhang1999_zh.tex fusiello2000_zh.tex && cd -
```

1. **第一条**：从 §1、§2 的输出重新生成报告插图。它按文件名读取原来 19 张照片的 §1 输出，所以只能在存有原照片的机器上运行。
2. **后两条**：重新编译报告和译稿的 PDF。
