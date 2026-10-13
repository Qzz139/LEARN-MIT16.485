<div align="center">

# Robotics Integration I · VNAV Labs

机器人集成课程 I（2026 秋）实验仓库：相机标定、ROS、四旋翼几何控制与竞速轨迹规划（LAB1 起基于 MIT VNAV）

![Ubuntu 20.04 · WSL2](https://img.shields.io/badge/Ubuntu-20.04%20%C2%B7%20WSL2-E95420?logo=ubuntu&logoColor=white)
![ROS Noetic](https://img.shields.io/badge/ROS-Noetic-22314E?logo=ros&logoColor=white)
![Unity 2019.3](https://img.shields.io/badge/Simulator-Unity%202019.3-000000?logo=unity&logoColor=white)
![macOS 26](https://img.shields.io/badge/macOS-26-000000?logo=apple&logoColor=white)
<br>
![C++11](https://img.shields.io/badge/C%2B%2B-11-00599C?logo=cplusplus&logoColor=white)
![Python 3.8 | 3.9](https://img.shields.io/badge/Python-3.8%20%7C%203.9-3776AB?logo=python&logoColor=white)
![OpenCV 4](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv&logoColor=white)
![LaTeX · Tufte](https://img.shields.io/badge/Report-LaTeX%20%C2%B7%20Tufte-008080?logo=latex&logoColor=white)

<img src="assets/lab4_race.gif" width="560" alt="LAB4：四旋翼在 Unity 模拟器中依次穿过 12 个门">

<sub>LAB4 竞速：12/12 门，6.78 s（官方 launch 复跑，模拟器视角）· 最快一次 6.74 s</sub>

</div>

## 实验一览

| 实验 | 内容 | 状态 | 关键结果 | 复现 / 报告 / 证据 |
| :-- | :-- | :-- | :-- | :-- |
| [LAB0](lab0/readme.md) | 张正友相机标定 · 双目校正与深度 · 两篇论文翻译 | ✅ 完成 | 手机相机重投影误差 0.942 px（19 张，4032×3024） | [复现](lab0/HUMANS.md) · [标定](lab0/reports/lab0_1_camera_calibration.pdf) · [双目](lab0/reports/lab0_2_stereo_depth.pdf) · [译文](lab0/translation/) |
| [LAB1](lab1/README.md) | Ubuntu 配置 · Shell · C++ 问答与实践 | ✅ 完成 | — | [复现](lab1/HUMANS.md) · [报告](lab1/report/lab1-report.pdf) · [截图](lab1/results/figures/) |
| [LAB2](lab2/README.md) | ROS 安装 · TF 驱动双机运动 · 四元数推导 | ✅ 完成 | — | [复现](lab2/HUMANS.md) · [报告](lab2/report/lab2_report.pdf) · [截图](lab2/results/screenshots/) |
| [LAB3](lab3/README.md) | 四旋翼几何控制器 · 圆轨迹跟踪 · 调参 | 🚧 报告撰写中 | 位置误差 RMS 4.3 cm，俯仰抖动 0.26° | [复现](lab3/HUMANS.md) · [结果](lab3/results/) |
| [LAB4](lab4/README.md) | 最小 snap 轨迹生成 · 12 门竞速 | 🚧 报告撰写中 | 12/12 门，最快 6.74 s，官方复跑 6.78 / 6.80 s | [复现](lab4/HUMANS.md) · [结果](lab4/results/) |
| LAB5 | 特征提取、匹配与跟踪（SIFT · FLANN · LK） | ⏳ 未开始 | | |
| LAB6 | 两视图位姿估计（5 点法 · 2D-2D · 3D-3D） | ⏳ 未开始 | | |
| LAB9 | VIO / SLAM 运行与轨迹评估（Kimera · ORB-SLAM3） | ⏳ 未开始 | | |

<sub>LAB4 穿门判据：机体中心距门中心 0.6 m 以内，且按顺序通过。模拟器里的门只是贴图，没有碰撞体，判据和计时口径见 [environment.txt](lab4/results/logs/environment.txt)。</sub>

## 演示

<table>
  <tr>
    <th>LAB0 · 双目深度</th>
    <th>LAB2 · TF 与双机轨迹</th>
  </tr>
  <tr>
    <td><img src="lab0/reports/figures/stereo_maps.jpg" width="400" alt="SGBM 视差图与相对深度图"></td>
    <td><img src="lab2/report/figures/traj_fixed_world_view.png" width="400" alt="RViz 中两架无人机的轨迹"></td>
  </tr>
  <tr>
    <td align="center"><sub>SGBM 视差（左）与相对深度（右），OpenCV aloe 双目数据</sub></td>
    <td align="center"><sub>蓝：AV1 在 world 系；红实线 / 虚线：AV2 在 world / av1 系</sub></td>
  </tr>
  <tr>
    <th>LAB3 · 几何控制器绕圈</th>
    <th>LAB4 · 竞速轨迹</th>
  </tr>
  <tr>
    <td><img src="assets/lab3_circle.gif" width="400" alt="RViz 中无人机沿圆轨迹飞行"></td>
    <td><img src="lab4/results/plots/official_run1.png" width="400" alt="竞速路径俯视图与高度曲线"></td>
  </tr>
  <tr>
    <td align="center"><sub>RViz：无人机沿圆轨迹飞行，红色为里程计轨迹</sub></td>
    <td align="center"><sub>官方复跑：俯视路径与 12 个门（左），高度跟踪（右）</sub></td>
  </tr>
</table>

## 环境

| 机器 | 用途 | 软件 |
| :-- | :-- | :-- |
| MacBook · macOS 26 | 主开发机：写代码、跑 LAB0、编译 LaTeX 报告 | Python 3.9.23 · NumPy 2.0.2 · OpenCV 4.12.0 |
| Windows 11 主机 · WSL2 | LAB1–4 的 Ubuntu / ROS 环境与 Unity 模拟器 | Ubuntu 20.04.6 · ROS Noetic · Python 3.8.10 · catkin（C++11）· RTX 4070 SUPER |

Mac 通过 SSH 操作 WSL；需要看模拟器画面时，用 Moonlight 串流 Windows 桌面。

> [!NOTE]
> 在 WSLg 下运行 VNAV 的 Unity 模拟器需要几处处理：加 `-force-gfx-direct` 单线程渲染、桥接节点首行改为 `python3`、修补桥接节点在模拟器时钟回退时的断言。细节见 [LAB3 environment.txt](lab3/results/logs/environment.txt) 和 [LAB4 environment.txt](lab4/results/logs/environment.txt)。

## 快速开始

**LAB0 双目深度**：纯 Python，数据已在仓库里，clone 后可以直接运行（已在 Python 3.9 下验证）。

```bash
python3.9 -m venv lab0/.venv && source lab0/.venv/bin/activate
python -m pip install -r lab0/requirements.txt
python lab0/code/stereo_depth.py --scale 0.5   # 结果写入 lab0/results/stereo/
```

**LAB4 竞速**：一次性准备（工作区、桥接修补、`env.sh`）见 [lab3/HUMANS.md](lab3/HUMANS.md) §0。每个终端先 `source ~/lab3_work/env.sh`，模拟器要在 Windows 桌面上的 Ubuntu 终端里启动。

```bash
# 终端 1：Unity 模拟器（WSLg 下必须加 -force-gfx-direct）
cd ~/vnav-builds/lab4 && env -u LIBGL_ALWAYS_SOFTWARE ./lab4.x86_64 -force-gfx-direct \
  -screen-fullscreen 0 -screen-width 1024 -screen-height 768
# 终端 2
roscore
# 终端 3：模拟器与 ROS 的桥接
roslaunch tesse_ros_bridge tesse_quadrotor_bridge.launch publish_collisions:=true
# 终端 4：轨迹生成 + 控制器（LAB3 增益）
roslaunch trajectory_generation traj_following.launch
# 终端 5：发布门的位姿，比赛开始，约 7 s 跑完
roslaunch planner_pkg traj_gen.launch
```

复位、穿门判据、一键脚本和提速过程见 [lab4/HUMANS.md](lab4/HUMANS.md)。其他实验同样按各自目录下的 `HUMANS.md` 复现：逐个给分点给出命令和参照结果；思路与分析在 `PLAN.md` 和报告里。

## 仓库结构

```text
.
├── lab0/ … lab4/    HUMANS.md（复现命令）· PLAN.md（思路与分析）· 代码、ROS 包与脚本 · results/（日志、图、视频、rosbag）· 报告
├── report-style/    报告共用的 Tufte LaTeX 导言区
├── assets/          README 用的演示 GIF
├── HUMANS.md        仓库导航
├── AGENTS.md        项目约定
├── syllabus.md      课程说明与评分
└── calendar.md      教学日历
```

## 致谢

- 实验题目、代码框架和 Unity 模拟器来自 MIT [VNAV](https://vnav.mit.edu/)（[MIT-SPARK/VNAV-labs](https://github.com/MIT-SPARK/VNAV-labs)，`VNAV2023` 标签）。
- LAB0 翻译的论文：Z. Zhang, *Flexible Camera Calibration by Viewing a Plane from Unknown Orientations*, ICCV 1999；A. Fusiello, E. Trucco, A. Verri, *A Compact Algorithm for Rectification of Stereo Pairs*, Machine Vision and Applications, 2000。

<sub>课程作业留档，仅供学习参考；请遵守课程的学术诚信要求。</sub>
