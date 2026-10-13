# Lab 3 手操复现说明

环境：Windows 主机上的 WSL 2 / Ubuntu-20.04（ROS Noetic，用户 `qz`）。参照值来自 2026-10-13 的记录，见 [results](results/)。重跑的数值会有小幅差异，不要冒充原始截图。原理与分析见 [PLAN.md](PLAN.md) 和报告。

| 给分点 | 节 | 证据 |
| --- | --- | --- |
| 简答题 1（25）、简答题 2（25） | §5 | [d1_tf2_check.txt](results/logs/d1_tf2_check.txt)、[d2_rank_check.txt](results/logs/d2_rank_check.txt) |
| 代码主体（20） | §2 | [final_circle.png](results/plots/final_circle.png)、[rviz_circle.mp4](results/video/rviz_circle.mp4) |
| av-desired 转动（10）、ROS 通信（10） | §3 | [av_desired_yaw.png](results/plots/av_desired_yaw.png)、[rqt_graph.png](results/screenshots/rqt_graph.png) |
| 调参（10） | §4 | [tuning.txt](results/logs/tuning.txt)、[jitter_comparison.txt](results/logs/jitter_comparison.txt)、[sim_old_vs_new.mp4](results/video/sim_old_vs_new.mp4) |

## 0. 一次性准备（已配好的主机跳过）

图形窗口只有在 WSL 虚拟机由 Windows 桌面启动时才会显示。所以开机后，先在 Windows 桌面打开 Ubuntu-20.04 终端（PowerShell 里运行 `wsl.exe --distribution Ubuntu-20.04`，不要只输入 `wsl`）。下面的 sudo 需要本人输入密码，首次编译需要 Windows 上的代理开着。

```bash
sudo apt install -y ros-noetic-ackermann-msgs python3-pip python3-scipy ffmpeg libgflags-dev
cd ~ && git clone https://github.com/Qzz139/26second-seme.git
mkdir -p ~/labs && cd ~/labs && curl -L -o VNAV2023.tar.gz https://github.com/MIT-SPARK/VNAV-labs/archive/refs/tags/VNAV2023.tar.gz && tar -xzf VNAV2023.tar.gz --strip-components=1
mkdir -p ~/vnav_ws/src && cd ~/vnav_ws && catkin init
# LAB3、LAB4 共用一个工作区；catkin_simple 和 mav_comm 用 dependencies/ 里的副本，不要另外复制
cp -r ~/labs/lab3/tesse-ros-bridge ~/labs/lab4/dependencies ~/vnav_ws/src/
cp -r ~/26second-seme/lab3/controller_pkg ~/26second-seme/lab4/planner_pkg ~/26second-seme/lab4/trajectory_generation_pkg ~/vnav_ws/src/
# 桥接修补：节点脚本改用 python3；LAB4 模拟器时钟清零时不再因断言崩溃
cd ~/vnav_ws/src/tesse-ros-bridge/ROS/src/tesse_ros_bridge
sed -i '1s|^#!/usr/bin/env python$|#!/usr/bin/env python3|' tesse_ros_node.py quadrotor_control_interface.py
python3 ~/26second-seme/lab4/scripts/patch_bridge.py tesse_ros_node.py
cd ~/vnav_ws/src/tesse-ros-bridge/tesse-interface && pip3 install --user --no-deps --no-build-isolation .
cd ~/vnav_ws && catkin build && source devel/setup.bash
mkdir -p ~/vnav-builds && cd ~/vnav-builds && curl -L -o lab3.zip https://vnav.mit.edu/material/lab3.zip && unzip -oq lab3.zip && chmod +x lab3/lab3.x86_64
# 辅助脚本与环境文件（LAB4 也会用到）
mkdir -p ~/lab3_work/bags ~/lab3_work/plots ~/lab3_work/logs
printf 'source /opt/ros/noetic/setup.bash\nsource ~/vnav_ws/devel/setup.bash\nexport DISPLAY=:0\n' > ~/lab3_work/env.sh
cp ~/26second-seme/lab3/scripts/*.py ~/26second-seme/lab3/scripts/run_trial.sh ~/lab3_work/ && chmod +x ~/lab3_work/run_trial.sh
```

编译应显示 `All N packages succeeded!`：这台主机上 N = 20（含 lab2 的包），全新环境是 19。每打开一个新终端，先运行 `source ~/lab3_work/env.sh`。

## 1. 启动（每次实验，开 4 个终端）

第一个终端必须是 Windows 桌面上的 Ubuntu 终端。`~/.bashrc` 里设置了 `LIBGL_ALWAYS_SOFTWARE=1`（给 rviz 用），启动模拟器时要去掉它，否则 Unity 会退回软件渲染：

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

`rostopic hz /current_state` 应约为 50 Hz。在模拟器窗口按 R，无人机复位到原点。

## 2. 代码主体：跟踪圆轨迹

```bash
roslaunch controller_pkg traj_tracking.launch
```

无人机起飞后追上圆轨迹（半径 5 m、高度 2 m、约 12.6 s 一圈），稳定绕圈。最终增益 8/5/10/2 写在 [traj_tracking.launch](controller_pkg/launch/traj_tracking.launch)。绕圈约 15 s 后录数据并分析：

```bash
rosbag record -O ~/lab3_work/circle.bag --duration=40 /current_state /desired_state /rotor_speed_cmds /tf
python3 ~/lab3_work/analyze_bag.py ~/lab3_work/circle.bag --plot ~/lab3_work/circle.png
python3 ~/lab3_work/jitter_check.py ~/lab3_work/circle.bag --skip 0
```

参照值见 [final_circle_summary.txt](results/logs/final_circle_summary.txt)：

| 指标 | 参照值 |
| --- | --- |
| 位置误差 RMS | 0.043 m，主要是约 4 cm 的高度稳态偏差 |
| 偏航误差 | 约 5.9° |
| 俯仰抖动 | 0.26° |
| 转速均值 | 约 46 rad/s |

定点悬停：把 `traj_publisher.cpp` 里的 `#define STATIC_POSE` 改成 1，重新编译（`catkin build controller_pkg`），再运行同一个 launch。目标点是 (0, 0, 2)、yaw 45°。测完改回 0。

## 3. av-desired 转动、ROS 通信

绕圈时运行：

```bash
rosrun tf tf_echo world av-desired
python3 ~/lab3_work/yaw_plot.py ~/lab3_work/circle.bag ~/lab3_work/av_desired_yaw.png
rosnode info /controller_node
rostopic hz /rotor_speed_cmds
rqt_graph
```

- **`tf_echo`**：打印的 yaw 角持续变化。rviz 里 `av-desired` 和 `base_link_gt` 两个坐标系一起转动，并且几乎重合。
- **`yaw_plot.py`**：期望偏航角以 −0.5 rad/s 匀速转动，无人机偏航滞后 5.86° ± 0.10°，参照 [av_desired_yaw.txt](results/logs/av_desired_yaw.txt)。
- **`rosnode info`**：控制器订阅 `/desired_state` 和 `/current_state`，发布 `/rotor_speed_cmds`。
- **话题频率**：`/rotor_speed_cmds` 约 99 Hz。
- **导出节点图 PNG**：`python3 ~/lab3_work/rosgraph_dot.py /tmp/g.dot && dot -Tpng /tmp/g.dot -o ~/lab3_work/rqt_graph.png`。

## 4. 调参

只开 §1 的模拟器和桥接，不要同时运行 §2 的 launch，`run_trial.sh` 会自己启动节点。每次运行都会复位、按给定增益飞行、录 bag 并分析，结果追加到 `~/lab3_work/tuning.txt`：

```bash
SKIP=8 ~/lab3_work/run_trial.sh demo_default circle 1 1 1 1 30
SKIP=8 ~/lab3_work/run_trial.sh demo_accurate circle 20 7 30 4 30
SKIP=8 ~/lab3_work/run_trial.sh demo_final circle 8 5 10 2 30
for b in demo_default demo_accurate demo_final; do python3 ~/lab3_work/jitter_check.py ~/lab3_work/bags/$b.bag; done
```

参数依次是：名称、`static` 或 `circle`、kx、kv、kr、komega、录制秒数。参照结果见 [jitter_comparison.txt](results/logs/jitter_comparison.txt)：

| 增益 | 现象 | 俯仰抖动 | 转速均值 |
| --- | --- | --- | --- |
| 1/1/1/1（模板默认） | 飞散，误差几十米 | — | — |
| 20/7/30/4 | 跟得紧，但高频颤振，螺旋桨频繁反转 | 1.15° | 约 20 rad/s |
| **8/5/10/2（最终）** | 平稳 | 0.26° | 约 46 rad/s |

全部 23 组调参实验见 [tuning.txt](results/logs/tuning.txt) 和 [plots](results/plots/)。

## 5. 简答题

```bash
cd ~/lab3_work && g++ -std=c++14 d1_tf2_check.cpp -I/opt/ros/noetic/include -I/usr/include/eigen3 -L/opt/ros/noetic/lib -ltf2 -lrostime -lcpp_common -Wl,-rpath,/opt/ros/noetic/lib -o d1_tf2_check && ./d1_tf2_check
python3 ~/lab3_work/d2_rank_check.py
```

- **简答题 1**：两次转换得到相同的四元数，`getYaw` 取回 0.700000，`max |R - R_tf2| = 0`。
- **简答题 2**：原布局的 F 矩阵 rank = 4；3、4 号螺旋桨反转后 rank = 3（偏航力矩恒等于 −0.0471 倍的滚转力矩）。(B) 的阻力补偿是纯推导，写在报告里。

## 6. 常见问题

| 现象 | 处理 |
| --- | --- |
| 模拟器或 rviz 窗口不出现 | `wsl --shutdown` 后，先从 Windows 桌面打开 Ubuntu 终端 |
| 桥接报 `/usr/bin/env: 'python'` | 没做 §0 的 `sed` 修补 |
| rviz 里 ROS Time 一直是 0 | roscore 被重启过，重启 rviz |
| 脚本里发 R 键没反应 | 用 `xdotool key --window <窗口号> r` |
| 绕圈时明显抖动 | 检查增益是否为 8/5/10/2 |
| 录屏 | 用 Win+Alt+R 或 OBS。WSLg 下 `ffmpeg -f x11grab` 抓到的是黑屏 |
