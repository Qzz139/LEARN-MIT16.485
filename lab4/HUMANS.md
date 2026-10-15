# LAB4 手操复现说明

只写操作步骤。原理和分析见 [PLAN.md](PLAN.md) 及报告。

## 环境前提

- Windows 主机的 WSL2 `Ubuntu-20.04`，ROS Noetic，工作区 `~/vnav_ws`。
- 模拟器在 `~/vnav-builds/lab4`，下载自 `vnav.mit.edu/material/lab4.zip`。
- `~/vnav_ws/src` 中需要有以下包：
  - 本仓库的 `lab3/controller_pkg`；
  - 本仓库的 `lab4/planner_pkg`、`lab4/trajectory_generation_pkg`；
  - VNAV2023 的 `tesse-ros-bridge` 和 `lab4/dependencies`。
- **所有命令都在 Windows 桌面上打开的 Ubuntu-20.04 终端里执行**，否则模拟器窗口不会显示。每开一个新终端，都要先运行：

```bash
source ~/vnav_ws/devel/setup.bash
```

### 一次性准备（已做过可跳过）

编译工作区：

```bash
cd ~/vnav_ws && catkin build
```

把桥接节点的两个脚本首行改为 `python3`（Ubuntu 20.04 没有 `python` 命令）：

```bash
sed -i '1s|^#!/usr/bin/env python$|#!/usr/bin/env python3|' ~/vnav_ws/src/tesse-ros-bridge/ROS/src/tesse_ros_bridge/tesse_ros_node.py ~/vnav_ws/src/tesse-ros-bridge/ROS/src/tesse_ros_bridge/quadrotor_control_interface.py
```

修补桥接节点的时间断言。LAB4 模拟器切换场景时会重置时钟，不修补的话收不到 `/current_state`。脚本在本仓库 `lab4/scripts/patch_bridge.py`，WSL 里已有一份：

```bash
python3 ~/lab4_work/patch_bridge.py ~/vnav_ws/src/tesse-ros-bridge/ROS/src/tesse_ros_bridge/tesse_ros_node.py
```

## 启动基础环境（每次实验前，各开一个终端）

1. 模拟器。必须加 `-force-gfx-direct`，否则在 WSLg 下会崩溃：

```bash
cd ~/vnav-builds/lab4 && env -u LIBGL_ALWAYS_SOFTWARE ./lab4.x86_64 -force-gfx-direct -screen-fullscreen 0 -screen-width 1024 -screen-height 768
```

2. roscore：

```bash
roscore
```

3. 桥接节点（同时打开碰撞上报）：

```bash
roslaunch tesse_ros_bridge tesse_quadrotor_bridge.launch publish_collisions:=true
```

4. 可选，用 rviz 俯视观看。先启动门的中转节点（给门的位姿补上坐标系，rviz 才能显示）：

```bash
python3 ~/lab4_work/gate_relay.py
```

再开 rviz：

```bash
rviz -d ~/lab4_work/lab4_topview.rviz
```

## 给分点复现

### ROS 通信 + 穿过 1 个门（Part 0：飞到第一个门悬停）

```bash
roslaunch planner_pkg static_point_test.launch
```

**应看到**：无人机飞到 0 号门，悬停在 (0.42, 3.17, 约 2.62)，机头朝 −90°。

**证据**：`results/screenshots/sim_part0_gate0.png`、`results/plots/part0_hover.png`、`results/logs/part0_summary.txt`。

### 穿过 6 个门 / 12 个门 / 竞速用时

终端 1–3 保持运行（上面的基础环境），再开 3 个终端，**严格按 A → B → C 的顺序操作**：

| 终端 | 作用 | 命令 |
|---|---|---|
| A（终端 5） | 控制器 + 轨迹生成 | `roslaunch trajectory_generation traj_following.launch` |
| B（终端 6） | 录 bag | `rosbag record -O ~/race.bag --duration=30 /current_state /desired_state /desired_traj_vertices /rotor_speed_cmds /tesse/collision /tf` |
| C（终端 7） | 发布门的位姿 = 发令枪 | `roslaunch planner_pkg traj_gen.launch` |

1. 确认无人机停在出生点 (0.4, 8.0) 的地面上（刚启动的模拟器就是这样）。
2. 终端 A 运行后，无人机**不会动**：轨迹生成节点要等收到门的位姿后才会生成轨迹。
3. 终端 B 开始录 bag，接着**在 30 秒内**到终端 C 运行命令。
4. 终端 C 一运行，无人机立即起飞，约 7 秒内依次穿过 12 个门，在最后一个门后方 6 m 处停下。
5. 等终端 B 录满 30 秒自动退出，然后在终端 B 分析：

```bash
python3 ~/lab4_work/race_check.py ~/race.bag --plot ~/race.png
```

**应看到**：`gates passed in order: 12/12` 和 `race time ... 6.7x s`，判据为距门心 0.6 m 以内。这个配置的成功率约 4/5，失败时会显示 `DNF`。

**再跑一次**：

1. 在终端 C、A 中按 Ctrl+C。
2. 在任一空闲终端让螺旋桨停转。模拟器会一直执行它收到的最后一条转速指令，所以必须先停转：

```bash
rostopic pub -1 /rotor_speed_cmds mav_msgs/Actuators "{angular_velocities: [0, 0, 0, 0]}"
```

3. 点一下模拟器窗口，按 **R** 复位，确认无人机回到出生点的地面上。
4. 重新按 A → B → C 的顺序操作。

**注意**：Part 0 的 `static_point_test.launch` 自带一个控制器，不能和终端 A 同时运行，要先在终端 A 按 Ctrl+C。

### 一键版（现场演示用）

前提是模拟器、roscore、桥接节点已经启动。下面这条命令会自动完成复位、两条 launch、录 bag、录模拟器画面、截取节点图和分析，结果保存在 `~/lab4_work/official/<名字>/`：

```bash
~/lab4_work/official_run.sh demo1
```

## 证据文件位置（`lab4/results/`）

| 给分点 | 文件 |
|---|---|
| ROS 通信 | `screenshots/rqt_graph.png`、`logs/ros_communication.txt` |
| 穿过 1 个门 | `screenshots/sim_part0_gate0.png`、`plots/part0_hover.png` |
| 穿过 6 个 / 12 个门 | `plots/Z_c14_r1.png`、`logs/fastest_run_summary.txt`、`bags/fastest_run_6.74s.bag` |
| 竞速用时 | `logs/race_attempts.csv`，最快一次 6.74 s；官方 launch 复跑 6.78 s 和 6.80 s，见 `logs/official_run*_summary.txt` |
| 视频 | `video/rviz_fastest_6.74s_replay.mp4`、`video/unity_view_official_6.78s.mp4` |
| 简答题 1、2 | `logs/d1_qp_check.txt`、`logs/d2_constraint_count.txt`（Mac 上运行 `python3 lab4/scripts/d1_qp_check.py` 即可复现） |
