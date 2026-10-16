# LAB4 手操复现说明

只写操作步骤。原理和分析见 [PLAN.md](PLAN.md) 及报告。

## 环境前提

- Windows 主机的 WSL2 `Ubuntu-20.04`，ROS Noetic，工作区 `~/vnav_ws`。
- 模拟器在 `~/vnav-builds/lab4`，下载自 `vnav.mit.edu/material/lab4.zip`。
- 本仓库克隆在 WSL 的 `~/LEARN-MIT16.485`。`~/vnav_ws/src` 里的三个包是指向克隆的软链接，另外两个是 VNAV2023 的原件：
  - `controller_pkg` → `~/LEARN-MIT16.485/lab3/controller_pkg`；
  - `planner_pkg`、`trajectory_generation_pkg` → `~/LEARN-MIT16.485/lab4/` 下的同名目录；
  - VNAV2023 的 `tesse-ros-bridge` 和 `lab4/dependencies`。
- **所有命令都在 Windows 桌面上打开的 Ubuntu-20.04 终端里执行**，否则模拟器窗口不会显示。每开一个新终端，都要先运行：

```bash
source ~/vnav_ws/devel/setup.bash
```

### 一次性准备（已做过可跳过）

克隆仓库，并在工作区里建立软链接（`~/vnav_ws/src` 里如果已有同名目录，先移走）：

```bash
git clone https://github.com/Qzz139/LEARN-MIT16.485.git ~/LEARN-MIT16.485
cd ~/vnav_ws/src && ln -s ~/LEARN-MIT16.485/lab3/controller_pkg controller_pkg && ln -s ~/LEARN-MIT16.485/lab4/planner_pkg planner_pkg && ln -s ~/LEARN-MIT16.485/lab4/trajectory_generation_pkg trajectory_generation_pkg
```

编译工作区：

```bash
cd ~/vnav_ws && catkin build
```

把桥接节点的两个脚本首行改为 `python3`（Ubuntu 20.04 没有 `python` 命令）：

```bash
sed -i '1s|^#!/usr/bin/env python$|#!/usr/bin/env python3|' ~/vnav_ws/src/tesse-ros-bridge/ROS/src/tesse_ros_bridge/tesse_ros_node.py ~/vnav_ws/src/tesse-ros-bridge/ROS/src/tesse_ros_bridge/quadrotor_control_interface.py
```

修补桥接节点的时间断言。LAB4 模拟器切换场景时会重置时钟，不修补的话收不到 `/current_state`（`race.sh` 也会自动检查并修补）：

```bash
python3 ~/LEARN-MIT16.485/lab4/scripts/patch_bridge.py ~/vnav_ws/src/tesse-ros-bridge/ROS/src/tesse_ros_bridge/tesse_ros_node.py
```

## 启动基础环境（每次实验前，各开一个终端）

1. 模拟器。必须加 `-force-gfx-direct -force-glcore33`，否则在 WSLg 下启动时大多会崩溃（终端显示 `[xcb] Unknown sequence number`）：

```bash
cd ~/vnav-builds/lab4 && env -u LIBGL_ALWAYS_SOFTWARE ./lab4.x86_64 -force-gfx-direct -force-glcore33 -screen-fullscreen 0 -screen-width 1024 -screen-height 768
```

如果模拟器在运行，但 Windows 桌面和任务栏上都看不到它的窗口（WSLg 偶尔会这样），在任一终端运行下面的命令，窗口就会重新出现：

```bash
W=$(xdotool search --name tesse_vnav_scenes | head -1); xdotool windowunmap --sync $W; xdotool windowmap --sync $W
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
python3 ~/LEARN-MIT16.485/lab4/scripts/gate_relay.py
```

再开 rviz：

```bash
rviz -d ~/LEARN-MIT16.485/lab4/rviz/lab4_topview.rviz
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
python3 ~/LEARN-MIT16.485/lab4/scripts/race_check.py ~/race.bag --plot ~/race.png
```

**应看到**：`gates passed in order: 12/12` 和 `race time ... 6.7x s`，判据为距门心 0.6 m 以内。这个配置一共完整飞了 18 次，成功 17 次（记录见 `logs/race_attempts.csv`、`logs/official_run*_summary.txt`、`logs/race_sh_runs.txt`）；失败时会显示 `DNF`。

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

在 Windows 桌面上打开的 Ubuntu-20.04 终端里运行。不需要事先手动启动任何东西：模拟器、roscore、桥接节点、rviz 中哪个没在运行，就自动启动哪个，然后复位、按官方的两条 launch 跑一次比赛、录 bag 并分析：

```bash
~/LEARN-MIT16.485/lab4/race.sh
```

**应看到**：终端最后打印 `gates passed in order: 12/12` 和 `race time ... 6.7x s`，退出码为 0。冷启动约 1 分钟，模拟器已在运行时约 30 秒。结果保存在 `~/lab4_runs/<时间>_c14/`，包括 `race.bag`、`race.png`、`summary.txt` 和 `params.txt`。

常用选项：

| 命令 | 作用 |
|---|---|
| `race.sh --cruise 12` | 改用 12 m/s 巡航（默认 14） |
| `race.sh --runs 3` | 连续跑 3 次 |
| `race.sh --record` | 同时录制模拟器视角的视频 `unity_view.mp4` |
| `race.sh --stop` | 关闭模拟器、桥接节点、rviz 和 roscore |

- 每次运行都会把模拟器窗口重新显示在屏幕左上角、置于最前。
- 跑完后模拟器保持运行，无人机悬停在出口点，再次运行会自动复位。
- 比赛中按 Ctrl+C，会停止录制和比赛节点，并让螺旋桨停转。
- 门被穿过后会变绿，并且一直保持绿色。想让门的颜色重置，就关掉模拟器窗口，再运行 `race.sh`，它会启动一个新的模拟器。

## 证据文件位置（`lab4/results/`）

| 给分点 | 文件 |
|---|---|
| ROS 通信 | `screenshots/rqt_graph.png`、`logs/ros_communication.txt` |
| 穿过 1 个门 | `screenshots/sim_part0_gate0.png`、`plots/part0_hover.png` |
| 穿过 6 个 / 12 个门 | `plots/Z_c14_r1.png`、`logs/fastest_run_summary.txt`、`bags/fastest_run_6.74s.bag` |
| 竞速用时 | `logs/race_attempts.csv`，最快一次 6.74 s；官方 launch 复跑 6.78 s 和 6.80 s，见 `logs/official_run*_summary.txt`；`race.sh` 13 次全部 12/12（6.74–6.78 s），见 `logs/race_sh_runs.txt` |
| 视频 | `video/rviz_fastest_6.74s_replay.mp4`、`video/unity_view_official_6.78s.mp4` |
| 简答题 1、2 | `logs/d1_qp_check.txt`、`logs/d2_constraint_count.txt`（Mac 上运行 `python3 lab4/scripts/d1_qp_check.py` 即可复现） |
