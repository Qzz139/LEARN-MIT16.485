# Lab 4 手操复现说明

环境与 Lab3 相同：WSL 2 / Ubuntu-20.04（ROS Noetic，用户 `qz`）。参照值来自 2026-10-13/14 的记录，见 [results](results/)。高速竞速有一定失败率，重跑的数值会有差异，不要冒充原始截图。原理与分析见 [PLAN.md](PLAN.md) 和报告。

| 给分点 | 节 | 证据 |
| --- | --- | --- |
| 简答题 1（25）、简答题 2（25） | §5 | [d1_qp_check.txt](results/logs/d1_qp_check.txt)、[d2_constraint_count.txt](results/logs/d2_constraint_count.txt) |
| 穿过 1 个门（10） | §2、§3 | [sim_part0_gate0.png](results/screenshots/sim_part0_gate0.png)、[part0_hover.png](results/plots/part0_hover.png) |
| 穿过 6 个门（10）、12 个门（20） | §3 | [fastest_run_summary.txt](results/logs/fastest_run_summary.txt)、[Z_c14_r1.png](results/plots/Z_c14_r1.png)、[视频](results/video/)、[rosbag](results/bags/fastest_run_6.74s.bag) |
| ROS 通信（10） | §3 | [rqt_graph.png](results/screenshots/rqt_graph.png)、[ros_communication.txt](results/logs/ros_communication.txt) |
| 用时排名加分 | §4 | [race_attempts.csv](results/logs/race_attempts.csv)（最快一次 6.74 s） |

## 0. 一次性准备

先完成 [Lab3 说明](../lab3/HUMANS.md) 的 §0（共用工作区、桥接修补、`env.sh`），再执行：

```bash
cd ~/vnav-builds && curl -L -o lab4.zip https://vnav.mit.edu/material/lab4.zip && unzip -oq lab4.zip && chmod +x lab4/lab4.x86_64
mkdir -p ~/lab4_work/bags ~/lab4_work/plots ~/lab4_work/logs ~/lab4_work/official
cp ~/26second-seme/lab4/scripts/*.py ~/26second-seme/lab4/scripts/*.sh ~/26second-seme/lab4/rviz/lab4_topview.rviz ~/26second-seme/lab3/scripts/rosgraph_dot.py ~/lab4_work/ && chmod +x ~/lab4_work/*.sh
```

## 1. 启动（每次实验）

第一个终端必须是 Windows 桌面上的 Ubuntu 终端。这个模拟器在 WSLg 下必须加 `-force-gfx-direct`（单线程渲染），否则启动就会崩溃，Player.log 里会出现 `xcb` 报错：

```bash
cd ~/vnav-builds/lab4 && env -u LIBGL_ALWAYS_SOFTWARE ./lab4.x86_64 -force-gfx-direct -screen-fullscreen 0 -screen-width 1024 -screen-height 768
```

```bash
roscore
```

```bash
roslaunch tesse_ros_bridge tesse_quadrotor_bridge.launch publish_collisions:=true
```

```bash
python3 ~/lab4_work/gate_relay.py & rviz -d ~/lab4_work/lab4_topview.rviz
```

- **检查桥接**：`rostopic hz /current_state` 应约为 50 Hz，无人机在出生点 (0.40, 8.00, 0.22)。
- **为什么要 `gate_relay.py`**：门位姿消息没有设置坐标系，这个中转节点补上 `world` 后转发到 `/gates_world`，rviz 才能把门画成黄色箭头。

门在模拟器里只是贴图，没有碰撞体积，尺寸也查不到。所以本实验的穿门判据是我们自己定的：机体中心依次进入每个门心 0.6 m 以内。用时从轨迹开始执行，算到首次进入最后一个门的 0.6 m 范围（见 [race_check.py](scripts/race_check.py)）。现场以助教的标准为准。

## 2. Part 0：飞到第一个门悬停

```bash
roslaunch planner_pkg static_point_test.launch
```

无人机飞到 0 号门中心 (0.42, 3.17, 2.67)，朝向 −90°，悬停在门里，这个门在模拟器里会变绿。用 `rostopic echo -n1 /current_state/pose/pose/position` 检查，应约为 (0.4226, 3.1652, 2.62)，比门心低约 5 cm，是稳态偏差。测完按 Ctrl-C 停掉。

## 3. 竞速：官方 launch（穿过 6 个门、12 个门，ROS 通信）

```bash
rostopic pub -1 /rotor_speed_cmds mav_msgs/Actuators "{angular_velocities: [0, 0, 0, 0]}"
```

模拟器会一直执行最后收到的转速指令，所以复位前先发一条全零指令停桨。然后在模拟器窗口按 R，确认无人机回到了出生点。之后在三个终端里依次运行：

```bash
roslaunch trajectory_generation traj_following.launch
```

```bash
rosbag record -O ~/lab4_work/race.bag --duration=16 /current_state /desired_state /desired_traj_vertices /rotor_speed_cmds /tesse/collision /tf
```

```bash
roslaunch planner_pkg traj_gen.launch
```

1. **第一条**：启动控制器和轨迹生成节点。这时无人机还停在地面，等待门的位姿。
2. **第二条**：开始录 bag，可选。
3. **第三条**：发布门的位姿，比赛从这一刻开始，约 7 s 跑完全程。

跑完后分析：

```bash
python3 ~/lab4_work/race_check.py ~/lab4_work/race.bag --plot ~/lab4_work/race.png
```

**参照结果**：输出 `gates passed in order: 12/12`，`race time` 约 6.7–6.8 s，最高速度约 17 m/s。起飞离地的瞬间会有 1–3 条 `Floor_01` 接触记录，之后没有碰撞。最快一次是 6.74 s，各门偏差在 0.14–0.55 m 之间；用官方 launch 复跑的两次分别是 6.78 s 和 6.80 s。

**最终配置**写在 [traj_following.launch](trajectory_generation_pkg/launch/traj_following.launch)：

| 参数 | 值 | 作用 |
| --- | --- | --- |
| `time_mode` | 1 | 每段时间按"距离 / 巡航速度"分配，第一段和最后一段加倍 |
| `v_max` | 14 | 巡航速度，单位 m/s |
| `exit_distance` | 6 | 终点设在最后一个门后方 6 m，最后一个门可以带速冲过去 |
| `use_omega_d` | true | 控制器使用期望角速度前馈 |
| 增益 | 8/5/10/2 | 和 Lab3 相同 |

**成功率**：这个配置一共飞了 5 次，成功 4 次。失败就复位重试；想要更大余量，可以把 `v_max` 改成 12，约 7.9 s。重新比赛前，先 Ctrl-C 停掉两个 launch。

**ROS 通信**：比赛结束后节点仍在运行，这时执行：

```bash
rosnode info /trajectory_generation_node
rostopic hz /desired_state
rqt_graph
```

通信链是 `traj_vertices_publisher` → `/desired_traj_vertices`（约 5 Hz）→ `trajectory_generation_node` → `/desired_state`（约 50 Hz）→ `controller_node` → `/rotor_speed_cmds`。节点图里如果出现红色的 `/rostopic_xxxx` 残留节点，先运行 `echo y | rosnode cleanup`。

**一键版**：只启动 §1 的模拟器、roscore 和桥接节点，然后运行 `~/lab4_work/official_run.sh run3`。脚本会自动完成停桨复位、比赛、录 bag、录模拟器画面、截节点图和话题信息，结果放在 `~/lab4_work/official/run3/`。

## 4. 提速过程（排名加分）

`run_race.sh` 会自动停桨、复位、按给定参数比赛并分析，结果追加到 `~/lab4_work/races.txt`。用法：

```
[TM=时间分配方式] [EXIT=出口距离] [OMD=1] ~/lab4_work/run_race.sh <名称> <v_max> <a_max> <kx> <kv> <kr> <komega> <录制秒数>
```

| 阶段 | 命令 | 参照结果 |
| --- | --- | --- |
| 模板默认 | `~/lab4_work/run_race.sh demo_template 8 4 8 5 10 2 35` | 35 s 内只过了 6 个门 |
| 按距离分配时间 | `TM=1 ~/lab4_work/run_race.sh demo_c8 8 8 8 5 10 2 30` | 12/12，12.00 s |
| + 出口点、较硬的增益 | `TM=1 EXIT=6 ~/lab4_work/run_race.sh demo_c9 9 8 12 6 20 3 20` | 12/12，10.52 s |
| + Ω_d 前馈 | `TM=1 EXIT=6 OMD=1 ~/lab4_work/run_race.sh demo_c10 10 8 8 5 10 2 18` | 12/12，9.44 s |
| 14 m/s | `TM=1 EXIT=6 OMD=1 ~/lab4_work/run_race.sh demo_c14 14 8 8 5 10 2 16` | 12/12，6.74 s（约 2/3 成功） |

只看规划、不起飞：`EXIT=6 ~/lab4_work/gen_only.sh 14 8 false 500 3 false 1`。它会打印规划的总时长和峰值速度、加速度，14 m/s 的配置是 7.66 s、峰值 16.8 m/s，参照 [plan_comparison.txt](results/logs/plan_comparison.txt)。全部 55 次尝试的汇总见 [race_attempts.csv](results/logs/race_attempts.csv)。

## 5. 简答题

```bash
python3 ~/26second-seme/lab4/scripts/d1_qp_check.py
python3 ~/26second-seme/lab4/scripts/d2_constraint_count.py
```

- **简答题 1**：只有位置约束时，1–3 次多项式的最优解都是 P = t，J = 1。加上 P′(1) = −2 后，2 次的最优解是 −3t² + 4t，J = 4；3 次的最优解是 −3.75t³ + 4.5t² + 0.25t，J = 2.125。
- **简答题 2**：minimum snap 的约束计数是 2k（路点）+ 6(k−1)（中间点导数连续）+ 6（两端固定导数）= 8k。脚本对 r = 2–5、k = 1–5 都验证了约束矩阵是方阵且满秩。

## 6. 常见问题

| 现象 | 处理 |
| --- | --- |
| 模拟器一启动就退出（`xcb` 报错） | 加 `-force-gfx-direct` |
| 收不到 `/current_state`，桥接报 `AssertionError` | 打 `patch_bridge.py` 修补（Lab3 说明 §0），再重启桥接 |
| rviz 里看不到门 | 运行 `gate_relay.py`，rviz 订阅 `/gates_world` |
| 复位后无人机乱飞 | 先发全零转速指令再按 R |
| 编译报重名包，或 `does not match the source` | `src/` 下有多余的 `catkin_simple` 或 `mav_comm`；删除后再清掉 `build/<包>` 和 `devel/.private/<包>` |
| 回放最快那次 | 停掉桥接节点，重启 rviz，运行 `rosbag play --clock -d 1 ~/26second-seme/lab4/results/bags/fastest_run_6.74s.bag`；录屏用 Win+Alt+R |
