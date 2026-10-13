# Lab 3 手操复现说明书

本说明书按本课程 Lab3 的给分点，告诉操作者每一步在哪个终端、输入什么命令、应当看到什么。目标环境是 **Windows x86-64 主机上的 WSL 2 / Ubuntu 20.04.6 + ROS Noetic**（用户 `qz`）。Mac 只用来阅读文件或远程连接。命令块里不写提示符，复制即可执行。

文中的参照值来自 2026-10-13 的实验记录（见 [results](results/)）。仿真每次重跑的数值会有小幅差异，**不要把重跑结果冒充原实验截图**。设计思路与分析见 [PLAN.md](PLAN.md)；英文正式报告另行提交，本文不替代报告。

| 给分点 | 分值 | 本文章节 | 仓库中的原始证据 |
| --- | --- | --- | --- |
| 简答题 1：ROS 中的旋转表示转换 | 25 | §7.1 | [d1_tf2_check.txt](results/logs/d1_tf2_check.txt) |
| 简答题 2：四旋翼结构与阻力补偿 | 25 | §7.2 | [d2_rank_check.txt](results/logs/d2_rank_check.txt) |
| 完成 av-desired 转动 | 10 | §4 | [av_desired_yaw.png](results/plots/av_desired_yaw.png)、[rviz_q1–q4](results/screenshots/) |
| 完成 ROS 通信 | 10 | §5 | [rqt_graph.png](results/screenshots/rqt_graph.png)、[ros_communication.txt](results/logs/ros_communication.txt) |
| 完成代码主体 | 20 | §3 | [final_circle.png](results/plots/final_circle.png)、[rviz_circle.mp4](results/video/rviz_circle.mp4) |
| 调参 | 10 | §6 | [tuning.txt](results/logs/tuning.txt)、[jitter_comparison.txt](results/logs/jitter_comparison.txt)、[sim_old_vs_new.mp4](results/video/sim_old_vs_new.mp4) |

## 0. 进入正确的终端

模拟器和 rviz 是图形程序。WSLg 只在 **WSL 虚拟机是从 Windows 桌面启动** 时，才会把窗口显示到桌面上。所以每次开机或执行过 `wsl --shutdown` 之后，先在 Windows 桌面上打开一个 Ubuntu-20.04 终端，再开其他终端或 SSH。从 Windows PowerShell 进入：

```powershell
wsl.exe --distribution Ubuntu-20.04
```

这台主机还装着另一个名为 `Ubuntu` 的发行版，**不要只输入 `wsl`**。从 Mac 远程操作时：

```bash
ssh -tt qz@100.84.51.48 wsl.exe --distribution Ubuntu-20.04
```

之后每打开一个新的 Ubuntu 终端，都先加载环境：

```bash
source /opt/ros/noetic/setup.bash
source ~/vnav_ws/devel/setup.bash
```

`~/.bashrc` 第 121 行设置了 `LIBGL_ALWAYS_SOFTWARE=1`（lab2 时为了让 rviz 显示网格模型而加）。rviz 照常用它，但**启动模拟器时必须去掉这个变量**，否则 Unity 会退回 CPU 软件渲染。§2 的命令已经处理好。

## 1. 一次性环境准备（已经配好的这台主机可以跳过）

### 1.1 系统包（需要 sudo，由本人输入密码）

```bash
sudo apt install -y ros-noetic-ackermann-msgs python3-pip python3-scipy ffmpeg libgflags-dev
```

依次是：桥接节点依赖的消息包、pip、scipy（桥接节点只用到 1.2 版就有的 `Rotation`，所以 apt 自带的 1.3.3 就够；这样做也避免 pip 把系统里的 numpy 一起升级）、录屏用的 ffmpeg、LAB4 编译日志库 glog 用的 gflags。

### 1.2 代码与工作区

```bash
cd ~ && git clone https://github.com/Qzz139/26second-seme.git
mkdir -p ~/labs && cd ~/labs
curl -L -o VNAV2023.tar.gz https://github.com/MIT-SPARK/VNAV-labs/archive/refs/tags/VNAV2023.tar.gz
tar -xzf VNAV2023.tar.gz --strip-components=1
mkdir -p ~/vnav_ws/src && cd ~/vnav_ws && catkin init
cp -r ~/labs/lab3/tesse-ros-bridge ~/labs/lab4/dependencies ~/vnav_ws/src/
cp -r ~/26second-seme/lab3/controller_pkg ~/26second-seme/lab4/planner_pkg ~/26second-seme/lab4/trajectory_generation_pkg ~/vnav_ws/src/
```

- **仓库与 MIT 代码**：前两行克隆本仓库，并取得 MIT 官方 `VNAV2023` 版本的代码（课程 README 指向 VNAV2021，两版 lab3/lab4 只有 tf2 迁移、模拟器路径等小差异，现在能下载到的模拟器对应 2023 版，见 [PLAN.md](PLAN.md)）。
- **工作区**：`catkin init` 只在新建工作区时需要。这台主机上的 `~/vnav_ws` 是 lab2 时就建好的。
- **最后两行组成 LAB3、LAB4 共用的工作区**：
  - `dependencies/` 里自带 `catkin_simple` 和 `mav_comm`，所以**不要再单独复制** `~/labs/lab3/catkin_simple`，否则会出现重名的包，编译报错；
  - 控制器、规划器和轨迹生成这三个包用本仓库的版本。

桥接节点要做两处本地修补，然后安装模拟器的 Python 接口并编译：

```bash
cd ~/vnav_ws/src/tesse-ros-bridge/ROS/src/tesse_ros_bridge
sed -i '1s|^#!/usr/bin/env python$|#!/usr/bin/env python3|' tesse_ros_node.py quadrotor_control_interface.py
python3 ~/26second-seme/lab4/scripts/patch_bridge.py tesse_ros_node.py
cd ~/vnav_ws/src/tesse-ros-bridge/tesse-interface && pip3 install --user --no-deps --no-build-isolation .
cd ~/vnav_ws && catkin build && source devel/setup.bash
```

- **`sed` 那一行**：Ubuntu 20.04 没有 `python` 命令，节点脚本首行的 `#!/usr/bin/env python` 会报 `/usr/bin/env: 'python': No such file or directory`，所以改成 `python3`。
- **`patch_bridge.py`**：LAB4 的模拟器在切换场景时会把时钟清零，原代码 `assert(prev_time < time)` 会让接收线程崩溃，表现为收不到 `/current_state`。这个脚本把断言改成重新同步时钟。LAB3 用不到，但打上也没有影响。
- **`--no-deps`**：tesse-interface 的 `setup.py` 会拉取 `enum34`，在 Python 3.8 上不需要，而且可能有害，所以不让 pip 自动装依赖。
- **首次 `catkin build`**：会从 GitHub 下载 glog、nlopt、yaml-cpp 的源码，需要 Windows 上的代理（v2rayN）开着。

**完成标准**：`catkin build` 显示 `All N packages succeeded!`。两个实验的包一起编译；这台主机上还有 lab2 的 `two_drones_pkg`，所以 N = 20，全新环境是 19。

### 1.3 模拟器

```bash
mkdir -p ~/vnav-builds && cd ~/vnav-builds
curl -L -o lab3.zip https://vnav.mit.edu/material/lab3.zip && unzip -oq lab3.zip && chmod +x lab3/lab3.x86_64
```

### 1.4 辅助脚本（§3–§6 的录数据、分析和自动实验要用）

```bash
mkdir -p ~/lab3_work/bags ~/lab3_work/plots ~/lab3_work/logs
cat > ~/lab3_work/env.sh <<'EOF'
source /opt/ros/noetic/setup.bash
source ~/vnav_ws/devel/setup.bash
export DISPLAY=:0
EOF
cp ~/26second-seme/lab3/scripts/*.py ~/26second-seme/lab3/scripts/run_trial.sh ~/lab3_work/
chmod +x ~/lab3_work/run_trial.sh
```

`env.sh` 会被 LAB3 和 LAB4 的所有脚本调用。复制过去的脚本都是本仓库 [scripts](scripts/) 里的原版。

## 2. 每次实验：启动仿真

依次开 4 个终端。第一个**必须是 Windows 桌面上的 Ubuntu 终端**（或者经 Moonlight 操作桌面）：

```bash
cd ~/vnav-builds/lab3 && env -u LIBGL_ALWAYS_SOFTWARE ./lab3.x86_64
```

```bash
roscore
```

```bash
roslaunch tesse_ros_bridge tesse_quadrotor_bridge.launch
```

```bash
rviz -d ~/vnav_ws/src/controller_pkg/rviz/lab3_topview.rviz
```

- **模拟器窗口**：应该出现一个 Unity 窗口，左上角显示帧率。这台主机实测约 390 fps，Player.log 里的渲染器是 `Renderer: D3D12 (NVIDIA GeForce RTX 4070 SUPER)`，参照截图 [sim_start.png](results/screenshots/sim_start.png)。
- **roscore 单独开一个终端**：这样之后重启桥接节点时，rviz 不会跟着断开（之前遇到过：重启 launch 后 rviz 里 ROS Time 一直是 0）。
- **验证桥接**：桥接节点启动后，在任意终端运行 `rostopic hz /current_state`，应该约为 50 Hz。
- **两种 rviz 视角**：`lab3_topview.rviz` 是俯视整个圆的配置；官方的原始配置 `rviz/lab3.rviz` 会显示紫色 IMU 箭头和 `base_link_gt`，参照 [rviz_start.png](results/screenshots/rviz_start.png)。

在模拟器窗口里按 **R** 可以把无人机复位到原点。从脚本发 R 键要用 `xdotool key --window <窗口号> r`，用 `windowactivate` 在 WSLg 下拿不到焦点。

## 3. 代码主体（20 分）：跟踪圆轨迹

第 5 个终端：

```bash
roslaunch controller_pkg traj_tracking.launch
```

- **launch 里启动的节点**：`traj_publisher` 发布圆轨迹（半径 5 m、高度 2 m、约 12.6 s 一圈，机头朝前进方向），`controller_node` 是我们实现的几何控制器。
- **增益**：在 [traj_tracking.launch](controller_pkg/launch/traj_tracking.launch) 里，最终值为 kx=8、kv=5、kr=10、komega=2。
- **应该看到的现象**：无人机起飞后迅速追上圆，稳定绕圈；rviz 里红色箭头轨迹画出整个圆。
- **代码位置**：实现在 [controller_node.cpp](controller_pkg/src/controller_node.cpp) 的 PART 1–5，主要有三点：
  - 坐标系按 ROS 的 z 轴朝上，推力和重力的符号与论文相反；
  - F2W 矩阵按模拟器的旋翼编号（1–4 号分别在机体系第 I–IV 象限）和反扭矩方向构建；
  - 世界系角速度要乘以 Rᵀ 换算到机体系。

录 40 s 数据并分析（第 6 个终端，起飞 15 s 以后再开始录）：

```bash
rosbag record -O ~/lab3_work/circle.bag --duration=40 /current_state /desired_state /rotor_speed_cmds /tf
python3 ~/lab3_work/analyze_bag.py ~/lab3_work/circle.bag --plot ~/lab3_work/circle.png
python3 ~/lab3_work/jitter_check.py ~/lab3_work/circle.bag --skip 0
```

参照值见 [final_circle_summary.txt](results/logs/final_circle_summary.txt)：

| 指标 | 参照值 |
| --- | --- |
| 位置误差 RMS | 0.043 m（最大 0.048 m） |
| 平均高度 | 1.958 m，比目标 2 m 低的 4 cm 是稳态偏差 |
| 偏航误差 | 约 5.9° |
| 俯仰抖动 | 0.26° |
| 转速均值 | 约 46 rad/s |

**定点悬停**（handout 建议在调圆轨迹之前先测）：把 `traj_publisher.cpp` 里的 `STATIC_POSE` 改成 1，重新编译，再启动同一个 launch。目标点是 (0, 0, 2)，yaw 45°。测完记得改回 0：

```bash
sed -i 's/^#define STATIC_POSE 0/#define STATIC_POSE 1/' ~/vnav_ws/src/controller_pkg/src/traj_publisher.cpp
cd ~/vnav_ws && catkin build controller_pkg && source devel/setup.bash
```

## 4. av-desired 转动（10 分）

`av-desired` 是 `traj_publisher` 广播的期望位姿 TF 坐标系。官方的 rviz 配置本来就打开了它的显示。绕圈时：

```bash
rosrun tf tf_echo world av-desired
python3 ~/lab3_work/yaw_plot.py ~/lab3_work/circle.bag ~/lab3_work/av_desired_yaw.png
```

- **`tf_echo`**：每秒打印一次 `av-desired` 的位姿，旋转部分（RPY 里的 yaw）随时间持续变化。
- **`yaw_plot.py`**：画出 `av-desired` 和 `base_link_gt`（无人机）的偏航角随时间变化，参照 [av_desired_yaw.txt](results/logs/av_desired_yaw.txt) 和 [av_desired_yaw.png](results/plots/av_desired_yaw.png)。期望偏航角以 −0.5000 rad/s 匀速转动，40 s 约转 1144°；无人机偏航稳定跟随，滞后 5.86° ± 0.10°。这个滞后来自控制律忽略了 Ω_d 项，理论值约为 (komega/kr) × 0.5 rad/s。
- **rviz 俯视视角**：两个坐标系几乎重合，连标签都叠在一起。每隔四分之一圈的截图见 [rviz_q1–q4](results/screenshots/)。

助教对这个给分点的具体检查方式还没确认（详见 [PLAN.md](PLAN.md)）。现场可以同时演示 rviz 和 `tf_echo`。

## 5. ROS 通信（10 分）

绕圈时运行：

```bash
rosnode info /controller_node
rostopic hz /desired_state
rostopic hz /rotor_speed_cmds
rqt_graph
```

- **`rosnode info`**：应列出订阅 `/desired_state`（`trajectory_msgs/MultiDOFJointTrajectoryPoint`）、`/current_state`（`nav_msgs/Odometry`），发布 `/rotor_speed_cmds`（`mav_msgs/Actuators`），接收方是 `/tesse/quadrotor_control_interface`。
- **话题频率参照**：`/desired_state` 和 `/rotor_speed_cmds` 约 99 Hz，`/current_state` 50 Hz。
- **`rqt_graph`**：会打开节点图窗口，参照 [rqt_graph.png](results/screenshots/rqt_graph.png)。
- **导出 PNG**：如果 rqt 窗口不方便截图，可以运行 `python3 ~/lab3_work/rosgraph_dot.py /tmp/g.dot && dot -Tpng -Gdpi=150 /tmp/g.dot -o ~/lab3_work/rqt_graph.png`。它调用的是 rqt_graph 自己的绘图库。

## 6. 调参（10 分）

`run_trial.sh` 一次完成一组对照实验：复位、按给定增益启动轨迹和控制器、录 bag、算误差、画图，结果追加到 `~/lab3_work/tuning.txt`。运行前要先按 §2 启动模拟器和桥接，**不要同时运行 §3 的 launch**（脚本会自己启动节点）：

```bash
SKIP=8 ~/lab3_work/run_trial.sh demo_default circle 1 1 1 1 30
SKIP=8 ~/lab3_work/run_trial.sh demo_accurate circle 20 7 30 4 30
SKIP=8 ~/lab3_work/run_trial.sh demo_final circle 8 5 10 2 30
for b in demo_default demo_accurate demo_final; do python3 ~/lab3_work/jitter_check.py ~/lab3_work/bags/$b.bag; done
```

- **参数**：依次是名称、`static` 或 `circle`、kx、kv、kr、komega、录制秒数。`SKIP=8` 表示前 8 s 是起飞追圈的过渡过程，不计入误差。
- **切换模式**：脚本会自动修改 `STATIC_POSE` 并重新编译。

三组对比的参照值见 [jitter_comparison.txt](results/logs/jitter_comparison.txt)。注意 `jitter_check` 这里的位置误差按消息接收时间对齐，比 §3 那种按时间戳对齐的方法略大：

| 增益 (kx, kv, kr, komega) | 现象 | 位置误差 RMS | 俯仰抖动 | 转速均值 |
| --- | --- | --- | --- | --- |
| 1, 1, 1, 1（模板默认） | 飞散，误差几十米 | 25 m | — | — |
| 20, 7, 30, 4（只看误差选出的第一轮结果） | 跟得紧但高频颤振，螺旋桨频繁反转 | 0.035 m | 1.15° | 约 18–21 rad/s |
| **8, 5, 10, 2（最终）** | 平稳 | 0.063 m | 0.26° | 约 46 rad/s |

- **对比视频**：两组增益的模拟器视角左右对比见 [sim_old_vs_new.mp4](results/video/sim_old_vs_new.mp4)。
- **完整调参过程**：23 组悬停和绕圈实验见 [tuning.txt](results/logs/tuning.txt)，对应的曲线在 [plots](results/plots/)。
- **规律**：
  - kr 太小，偏航慢、水平方向缓慢发散（A1）；
  - komega 太大，会失稳（B3）；
  - kv 或 kx 相对 kr 太大，会出现约 1 Hz 的振荡（C4、C5）。

  用实测惯量 J_yy ≈ 0.18 kg·m²（见 [inertia_fit.txt](results/logs/inertia_fit.txt)）可以定量解释这些现象：姿态环的速度至少要是位置环的约 2.5 倍。

另外两个选做的分析脚本：`frame_check.py` 验证 `/current_state` 里的速度和角速度都是世界系的（[frame_check.txt](results/logs/frame_check.txt)）；`inertia_fit.py` 估计转动惯量。用法都是 `python3 ~/lab3_work/<脚本>.py <bag>`。

## 7. 简答题

### 7.1 简答题 1（25 分）：tf2 与 msg 互转

```bash
cd ~/lab3_work
g++ -std=c++14 d1_tf2_check.cpp -I/opt/ros/noetic/include -I/usr/include/eigen3 -L/opt/ros/noetic/lib -ltf2 -lrostime -lcpp_common -Wl,-rpath,/opt/ros/noetic/lib -o d1_tf2_check
./d1_tf2_check
```

程序里每一问的答案都是一行代码，见 [d1_tf2_check.cpp](scripts/d1_tf2_check.cpp)：`tf2::fromMsg`、`tf2::toMsg`、`getW()`、`tf2::getYaw`、`fromMsg` 加 `toRotationMatrix()`。输出应与 [d1_tf2_check.txt](results/logs/d1_tf2_check.txt) 一致：两次转换得到相同的四元数 (0.080904, −0.076611, 0.345445, 0.931801)，`getYaw` 取回 0.700000，`max |R - R_tf2| = 0`。

### 7.2 简答题 2（25 分）：螺旋桨布局与阻力补偿

```bash
python3 ~/lab3_work/d2_rank_check.py
```

原布局的 F 矩阵 rank = 4；把 3、4 号螺旋桨反转后 rank = 3，偏航力矩恒等于 −0.0471 倍的滚转力矩，单独的偏航力矩无法产生，参照 [d2_rank_check.txt](results/logs/d2_rank_check.txt)。(B) 的阻力补偿是纯推导：在期望推力里减去 R·D·(v_b)²。这一部分写在报告里，不需要程序。

## 8. 录屏与截图

- **最简单的方法**：用 Windows 自带的 Xbox Game Bar（Win+Alt+R）或 OBS 录桌面上的 rviz 或模拟器窗口。
- **在 WSL 里截图**：

  ```bash
  WID=$(xwininfo -root -tree | grep -E 'lab3_topview.rviz.*RViz' | head -1 | awk '{print $1}')
  import -window $WID ~/lab3_work/rviz.png
  ( end=$((SECONDS+15)); while [ $SECONDS -lt $end ]; do import -window $WID ppm:-; done ) | ffmpeg -nostdin -y -f image2pipe -c:v ppm -use_wallclock_as_timestamps 1 -i - -vf "scale=1280:-2,format=yuv420p" -r 15 -c:v libx264 ~/lab3_work/rviz.mp4
  ```

  第一行找到 rviz 窗口号，第二行截一张图，第三行按窗口抓帧录 15 s 视频。WSLg 下 `ffmpeg -f x11grab` 直接抓屏得到的是全黑画面，所以要按窗口抓。在脚本里用 ffmpeg 时一定要加 `-nostdin`，否则它会吃掉后面的脚本内容。

## 9. 常见问题

| 现象 | 原因与处理 |
| --- | --- |
| 模拟器或 rviz 窗口不出现 | WSL 虚拟机是从 SSH 启动的。执行 `wsl --shutdown`，再先从 Windows 桌面打开 Ubuntu 终端 |
| 桥接报 `/usr/bin/env: 'python'` | §1.2 的 `sed` 修补没做 |
| rviz 里 ROS Time 一直是 0 | roscore 被重启过，rviz 还连着旧 master。重启 rviz（roscore 要单独开一个终端） |
| 按 R 没反应（脚本里） | 用 `xdotool key --window <id> r`，不要用 `windowactivate` |
| 无人机起飞就翻 | 先 Ctrl-C 停掉控制器，按 R 复位，再重新启动 launch |
| 绕圈时明显抖动 | 用错了增益，最终增益是 8/5/10/2（§6） |
| 首次 `catkin build` 下载失败 | Windows 上的代理（v2rayN）没开 |
