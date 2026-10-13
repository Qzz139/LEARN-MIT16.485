# Lab 2 手操复现说明

环境：Windows 主机上的 WSL 2 / Ubuntu-20.04.6（用户 `qz`），ROS Noetic，代码基于 MIT `VNAV2023`。参照值来自 2026-09-25 的记录，见 [results](results/)。思路见 [PLAN.md](PLAN.md)，报告见 [lab2_report.pdf](report/lab2_report.pdf)。

| 给分点 | 节 | 证据 |
| --- | --- | --- |
| 安装 ROS（20） | §0 | [ros_install_summary.txt](results/logs/ros_install_summary.txt)、[turtlesim_teleop.png](results/screenshots/turtlesim_teleop.png) |
| 控制无人机运动（40） | §1、§2 | [static_scene.png](results/screenshots/static_scene.png)、[dynamic_world_a.png](results/screenshots/dynamic_world_a.png)、[dynamic_nodes_topics.txt](results/logs/dynamic_nodes_topics.txt)、[tf_tree_dynamic.pdf](results/screenshots/tf_tree_dynamic.pdf) |
| 轨迹（30） | §2 | [traj_fixed_world.png](results/screenshots/traj_fixed_world.png)、[traj_fixed_av1.png](results/screenshots/traj_fixed_av1.png) |
| 数学推导（10） | §3 | [check_tf_summary.txt](results/logs/check_tf_summary.txt)、报告 |
| 四元数性质（10） | §3 | [quaternion_check.txt](results/logs/quaternion_check.txt)、报告 |

## 0. 安装 ROS 与验证（已装好的主机跳过安装）

模拟器和 rviz 的窗口要显示在桌面上，所以先在 Windows 桌面打开 Ubuntu-20.04 终端。安装命令（需要 sudo）：

```bash
sudo apt-get update && sudo apt-get install -y curl ca-certificates lsb-release
curl -fsSL -o /tmp/ros-apt-source.deb https://github.com/ros-infrastructure/ros-apt-source/releases/download/1.3.0/ros-apt-source_1.3.0.focal_all.deb
sudo apt-get install -y /tmp/ros-apt-source.deb && sudo apt-get update
sudo apt-get install -y ros-noetic-desktop-full python3-rosdep python3-catkin-tools build-essential
sudo rosdep init; rosdep update --include-eol-distros
```

Noetic 已经停止维护，所以 `rosdep update` 要加 `--include-eol-distros`。原始记录：安装了 234 个 ros-noetic 包，0 个错误。

验证 ROS 能用：开三个终端，每个终端先运行 `source /opt/ros/noetic/setup.bash`，再分别运行下面三条：

```bash
roscore
```

```bash
rosrun turtlesim turtlesim_node
```

```bash
rosrun turtlesim turtle_teleop_key
```

在第三个终端里按方向键，海龟会跟着移动，参照截图 [turtlesim_teleop.png](results/screenshots/turtlesim_teleop.png)。

## 1. 工作区与静态场景

```bash
cd ~ && git clone https://github.com/Qzz139/26second-seme.git
mkdir -p ~/vnav_ws/src && cp -r ~/26second-seme/lab2/two_drones_pkg ~/vnav_ws/src/
cd ~/vnav_ws && catkin init && catkin build && source devel/setup.bash
roslaunch two_drones_pkg two_drones.launch static:=True
```

- **静态场景的现象**：rviz 里两架无人机静止不动，AV1 在 (1, 0, 0)，AV2 在 (0, 0, 1)，参照 [static_scene.png](results/screenshots/static_scene.png)。
- **节点**：用 `rosnode list` 和 `rostopic info /visuals` 查看，有两个静态 TF 发布节点 `av1broadcaster`、`av2broadcaster`，加上 `plots_publisher_node` 和 `rviz`，参照 [static_nodes_topics.txt](results/logs/static_nodes_topics.txt)。
- **代码**：仓库里的包已经包含完成后的代码，以及一处模板修正：`plots_publisher_node.cpp` 里，tf 的 buffer 必须声明在 listener 之前，否则会按错误的顺序初始化。

## 2. 动态场景与三条轨迹

```bash
roslaunch two_drones_pkg two_drones.launch
```

不带 `static:=True` 时，launch 会改为启动我们实现的 `frames_publisher_node`，以 50 Hz 发布两架无人机的 TF。

**运动**：

- AV1 在 xy 平面沿单位圆运动，y 轴始终沿切线方向；
- AV2 在 xz 平面沿抛物线段 z = 1 − 2x² 往返运动，姿态保持不变。

**三条轨迹**（在 rviz 左侧把 Fixed Frame 在 `world` 和 `av1` 之间切换）：

| 轨迹 | 参考系 | 形状 |
| --- | --- | --- |
| AV1，蓝色实线 | `world` | 圆 |
| AV2，红色实线 | `world` | 抛物线 |
| AV2，红色虚线 | `av1` | 斜平面 z − 2y = 1 内的椭圆 |

参照截图 [traj_fixed_world.png](results/screenshots/traj_fixed_world.png) 和 [traj_fixed_av1.png](results/screenshots/traj_fixed_av1.png)，TF 树见 [tf_tree_dynamic.pdf](results/screenshots/tf_tree_dynamic.pdf)。

## 3. 数学推导与四元数的数值校验

动态场景运行时，在 Ubuntu 里执行第一条；第二条不需要 ROS，Mac 上也能跑：

```bash
python3 ~/26second-seme/lab2/scripts/check_tf.py 12 /tmp/tf_samples.csv
python3 ~/26second-seme/lab2/scripts/quaternion_check.py
```

- **`check_tf.py`**：从 TF 实时采样，和报告里推出的解析式逐项对比，所有残差都应在 1e-15 量级（[check_tf_summary.txt](results/logs/check_tf_summary.txt)）。具体包括：
  - 单位圆和抛物线的方程；
  - 相对位置的解析式；
  - 相对轨迹所在的平面 z − 2y = 1；
  - 椭圆的两个半轴 1/2 和 √5/2（实测 x_p ∈ [−0.5, 0.5]，y_p ∈ [−1.118, 1.118]）。
- **`quaternion_check.py`**：用 1000 组随机四元数验证 Ω₁、Ω₂ 的正交性、单位元关系和交换关系，误差在 1e-15 量级。同时说明课件里印的那个 Ω₁ 不是正交矩阵（误差 0.9998），参照 [quaternion_check.txt](results/logs/quaternion_check.txt)。

推导过程本身写在报告里。
