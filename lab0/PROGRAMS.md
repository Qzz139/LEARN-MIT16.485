# Lab0 程序使用说明

从仓库根目录运行命令。程序使用 Python 3.10+、NumPy 和 OpenCV；无需图形界面。

```bash
python3 -V                         # 确认版本至少为 3.10
python3 -m venv lab0/.venv
source lab0/.venv/bin/activate
python -m pip install -r lab0/requirements.txt
```

## Lab0-1：手机相机内参标定

把同一手机镜头、同一分辨率拍摄的棋盘照片放到 `lab0/data/phone/`，然后运行：

```bash
python lab0/code/calibrate_phone.py --images lab0/data/phone --square-size-m 0.03
```

附件棋盘有 **9×6 个方格，内部角点为 8×5**；这也是程序默认值。`0.03` 是方格实际边长的米数，打印后应先用尺测量，再按实测值修改。建议拍摄至少 20 张不同倾角、距离和画面位置的照片；程序默认至少需要 10 张成功检测的图像。若需要其他棋盘规格，可设置 `--columns`、`--rows`。如果照片分辨率不一致，程序会跳过不一致的图像。

输出在 `lab0/results/calibration/`：

| 文件 | 内容 |
| --- | --- |
| `summary.json` | 相机矩阵、畸变系数、全局及逐图重投影误差、失败图像列表 |
| `calibration.npz` | 程序可读取的内参、畸变参数及各图的姿态向量 |
| `corners/*.png` | 检测到的棋盘角点，适合放入报告核对 |
| `before_after.png` | 第一张有效照片去畸变前后对比 |

`K` 中的焦距以像素计；棋盘方格的米制单位主要决定每张棋盘相对相机的平移尺度。标定结果只属于这台手机在本次镜头、焦距和图像尺寸设置下的相机模型。

## Lab0-2：OpenCV Aloe 双目示例

首次执行 `--sample` 会从 OpenCV 官方仓库下载 `aloeL.jpg`、`aloeR.jpg` 到 `lab0/data/stereo/`；后续运行复用本地文件，需要联网下载的只有第一次。示例图像已经适合按水平扫描线匹配：

```bash
python lab0/code/stereo_depth.py --sample --scale 0.5
```

也可用自己的**已校正**双目图像：

```bash
python lab0/code/stereo_depth.py --left left.png --right right.png --num-disparities 128 --block-size 5
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
python lab0/code/stereo_depth.py --left left.png --right right.png \
  --focal-px 800 --baseline-m 0.10
```

这里的 `800` 和 `0.10` 仅示范参数写法，不能直接用于 Aloe 或其他数据。此模式会输出 `depth_m.npy`。如果左右主点横坐标不同，还需加 `--cx-difference-px`，其值为 `cx_left - cx_right`；程序按 `Z = f·B / (d - cx_difference)` 换算。若图像用 `--scale 0.5` 缩小，`--focal-px` 和 `--cx-difference-px` 也必须缩小到原值的一半。

报告中应附上输入来源、运行命令、主要参数、角点或视差图、误差与失败区域分析。两篇论文的翻译及两份报告仍按 [Lab0 要求](readme.md) 单独完成；程序输出提供实验记录，不能代替实际拍摄与报告分析。

参考：[OpenCV 相机标定教程](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html)、[OpenCV 官方 Aloe 双目示例](https://github.com/opencv/opencv/blob/4.x/samples/python/stereo_match.py)。
