# Lab0 程序使用说明

从仓库根目录运行命令。程序已在当前环境的 **Python 3.9.23、NumPy 2.0.2、OpenCV 4.12.0** 下验证；无需图形界面。当前环境已有依赖，可直接运行下面两个实验命令。若换到尚未安装依赖的环境，再执行：

```bash
python3.9 -V
python3.9 -m venv lab0/.venv
source lab0/.venv/bin/activate
python -m pip install -r lab0/requirements.txt
```

## Lab0-1：手机相机内参标定

本机的 19 张手机原图位于 `lab0/data/phone/`，格式均为 HEIC；已用 `heif-convert` 转为 `lab0/data/phone_jpg/` 中的 JPG。手机原图和转换图体积较大，未推送到 GitHub；从仓库克隆后需放入自己的棋盘照片。程序读取 JPG，不直接读取 HEIC。若使用 HEIC，可在仓库根目录转换：

```bash
mkdir -p lab0/data/phone_jpg
for file in lab0/data/phone/*.HEIC; do
  heif-convert --quiet -q 95 "$file" "lab0/data/phone_jpg/$(basename "$file" .HEIC).jpg"
done
```

然后运行本次手机标定：

```bash
python3.9 lab0/code/calibrate_phone.py --images lab0/data/phone_jpg --square-size-m 0.025
```

附件棋盘有 **9×6 个方格，内部角点为 8×5**；这也是程序默认值。本次棋盘显示在笔记本屏幕上，`0.025` 应为屏幕上**实测**的单格边长，不能直接使用 PDF 标注的打印尺寸。现有 19 张照片均成功检测，满足程序默认的至少 10 张有效图像要求；拍摄角度越多样，标定通常越稳健。若需要其他棋盘规格，可设置 `--columns`、`--rows`。如果照片分辨率不一致，程序会跳过不一致的图像。

输出在 `lab0/results/calibration/`：

| 文件 | 内容 |
| --- | --- |
| `summary.json` | 相机矩阵、畸变系数、全局及逐图重投影误差、失败图像列表 |
| `calibration.npz` | 程序可读取的内参、畸变参数及各图的姿态向量 |
| `corners/*.png` | 检测到的棋盘角点，适合放入报告核对 |
| `before_after.png` | 第一张有效照片去畸变前后对比 |

GitHub 上保留 `summary.json`、`calibration.npz` 和报告内的精选角点、去畸变图；完整逐图角点图和原尺寸去畸变图仅在本机结果目录中。`K` 中的焦距以像素计；棋盘方格的米制单位主要决定每张棋盘相对相机的平移尺度。标定结果只属于这台手机在本次镜头、焦距和图像尺寸设置下的相机模型。

## Lab0-2：OpenCV Aloe 双目示例

首次执行 `--sample` 会从 OpenCV 官方仓库下载 `aloeL.jpg`、`aloeR.jpg` 到 `lab0/data/stereo/`；后续运行复用本地文件，需要联网下载的只有第一次。示例图像已经适合按水平扫描线匹配：

```bash
python3.9 lab0/code/stereo_depth.py --sample --scale 0.5
```

也可用自己的**已校正**双目图像：

```bash
python3.9 lab0/code/stereo_depth.py --left left.png --right right.png --num-disparities 128 --block-size 5
```

程序用 `StereoSGBM` 计算视差；OpenCV 的定点输出除以 16 转成像素视差。`--num-disparities` 必须是 16 的倍数；`--block-size` 是不小于 3 的奇数。左右图必须尺寸一致，并在输入前完成立体校正。`rectified_pair_check.png` 上的水平线可辅助检查，但它本身不能证明每处对应点都准确对齐。

输出在 `lab0/results/stereo/`：

| 文件 | 内容 |
| --- | --- |
| `rectified_pair_check.png` | 左右图并排和水平参考线 |
| `disparity_px.npy`、`disparity.png` | 原始像素视差和可视化图 |
| `valid_mask.png` | 用于深度换算的有效像素位置 |
| `depth_approx_baseline_units.npy`、`depth_preview.png` | 默认示例的**近似、无米制尺度**深度及预览图 |
| `summary.json` | 参数、有效像素比例和深度单位说明 |

默认深度使用 OpenCV 官方 Aloe 示例的假设焦距 `0.8 × 图像宽度`，并把基线设为 `1` 个任意单位。因此 `depth_approx_baseline_units.npy` 可展示近远关系，不能解释成“多少米”。有**与这对图像配套、并已按图像缩放比例换算**的校正后焦距与真实基线时，才可运行：

```bash
python3.9 lab0/code/stereo_depth.py --left left.png --right right.png \
  --focal-px 800 --baseline-m 0.10
```

这里的 `800` 和 `0.10` 仅示范参数写法，不能直接用于 Aloe 或其他数据。此模式会输出 `depth_m.npy`。如果左右主点横坐标不同，还需加 `--cx-difference-px`，其值为 `cx_left - cx_right`；程序按 `Z = f·B / (d - cx_difference)` 换算。若图像用 `--scale 0.5` 缩小，`--focal-px` 和 `--cx-difference-px` 也必须缩小到原值的一半。

报告中应附上输入来源、运行命令、主要参数、角点或视差图、误差与失败区域分析。两篇[中文论文译稿](translation/)和两份[英文实验报告](reports/)按 [Lab0 要求](readme.md) 分开提交；程序输出和精简结果供复核。

参考：[OpenCV 相机标定教程](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html)、[OpenCV 官方 Aloe 双目示例](https://github.com/opencv/opencv/blob/4.x/samples/python/stereo_match.py)。
