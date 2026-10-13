# Lab 4 手操复现说明书

本说明书按本课程 Lab4 的给分点，告诉操作者每一步在哪个终端、输入什么命令、应当看到什么。环境与 Lab3 相同：**Windows 主机上的 WSL 2 / Ubuntu 20.04.6 + ROS Noetic**（用户 `qz`）。命令块里不写提示符，复制即可执行。

文中的参照值来自 2026-10-13/14 的实验记录（见 [results](results/)）。仿真每次重跑会有差异，高速竞速还有一定的失败率，**不要把重跑结果冒充原实验截图**。设计思路与分析见 [PLAN.md](PLAN.md)；英文正式报告另行提交。

| 给分点 | 分值 | 本文章节 | 仓库中的原始证据 |
| --- | --- | --- | --- |
| 简答题 1：单段最小速度 QP | 25 | §7.1 | [d1_qp_check.txt](results/logs/d1_qp_check.txt) |
| 简答题 2：多段 minimum snap 约束计数 | 25 | §7.2 | [d2_constraint_count.txt](results/logs/d2_constraint_count.txt) |
| ROS 通信 | 10 | §5 | [rqt_graph.png](results/screenshots/rqt_graph.png)、[ros_communication.txt](results/logs/ros_communication.txt) |
| 穿过 1 个门 | 10 | §3、§4 | [sim_part0_gate0.png](results/screenshots/sim_part0_gate0.png)、[part0_hover.png](results/plots/part0_hover.png) |
| 穿过 6 个门 | 10 | §4 | [fastest_run_summary.txt](results/logs/fastest_run_summary.txt) |
| 穿过 12 个门 | 20 | §4 | [Z_c14_r1.png](results/plots/Z_c14_r1.png)、[视频](results/video/)、[rosbag](results/bags/fastest_run_6.74s.bag) |
| 用时排名加分 | 10/8/6/4/2 | §6 | [race_attempts.csv](results/logs/race_attempts.csv)（最快一次 6.74 s） |

## 0. 前提与一次性准备

先完成 [Lab3 说明书](../lab3/HUMANS.md) 的 §0 和 §1，Lab4 要用的东西那里已经一起配好了：LAB3 和 LAB4 合用的工作区（含 `dependencies/`）、桥接节点的两处修补、`~/lab3_work/env.sh`。另外还需要 Lab4 的模拟器和辅助脚本：

```bash
cd ~/vnav-builds && curl -L -o lab4.zip https://vnav.mit.edu/material/lab4.zip && unzip -oq lab4.zip && chmod +x lab4/lab4.x86_64
mkdir -p ~/lab4_work/bags ~/lab4_work/plots ~/lab4_work/logs ~/lab4_work/official
cp ~/26second-seme/lab4/scripts/*.py ~/26second-seme/lab4/scripts/*.sh ~/26second-seme/lab4/rviz/lab4_topview.rviz ~/lab4_work/
cp ~/26second-seme/lab3/scripts/rosgraph_dot.py ~/lab4_work/
chmod +x ~/lab4_work/*.sh
```

如果工作区是先按 lab3 原始说明搭的，`src/` 下还单独放着 `catkin_simple` 或 `mav_comm`，要先删掉，因为 `dependencies/` 里已经各有一份，重名会导致编译失败。删掉后它们留下的旧编译缓存也要清理，否则会报 `CMake Error: The source directory ... does not exist`：

```bash
cd ~/vnav_ws && rm -rf src/catkin_simple src/mav_comm
rm -rf build/catkin_simple build/mav_comm build/mav_msgs build/mav_planning_msgs build/mav_state_machine_msgs build/mav_system_msgs devel/.private/mav_comm
catkin build && source devel/setup.bash
```

## 1. 每次实验：启动仿真

第一个终端**必须是 Windows 桌面上的 Ubuntu 终端**（原因见 Lab3 说明书 §0）：

```bash
cd ~/vnav-builds/lab4 && env -u LIBGL_ALWAYS_SOFTWARE ./lab4.x86_64 -force-gfx-direct -screen-fullscreen 0 -screen-width 1024 -screen-height 768
```

这个模拟器是 2020 年打包的 Unity 2019 版本。在 WSLg 下**不加 `-force-gfx-direct`（强制单线程渲染）就会崩溃**，Player.log 里会出现 `[xcb] Unknown sequence number ... XInitThreads has not been called`。后面三个参数让它以 1024×768 窗口运行；默认是 4K 全屏，只有约 22 fps。

再依次开三个终端：

```bash
roscore
```

```bash
roslaunch tesse_ros_bridge tesse_quadrotor_bridge.launch publish_collisions:=true
```

```bash
python3 ~/lab4_work/gate_relay.py & rviz -d ~/lab4_work/lab4_topview.rviz
```

- **检查桥接**：`rostopic hz /current_state` 应约为 50 Hz；`rostopic echo -n1 /current_state/pose/pose/position` 应显示无人机在出生点 (0.40, 8.00, 0.22)，初始朝向约 −166°。
- **`publish_collisions:=true`**：让碰撞信息发布到 `/tesse/collision`。
- **`gate_relay.py`**：MIT 的门位姿发布节点发出的消息没有设置坐标系（`frame_id` 为空），rviz 画不出门。这个中转节点补上 `frame_id = world` 后，转发到 `/gates_world`。
- **rviz 俯视配置**：可以看到整条赛道，门是黄色箭头（指向穿门方向），飞行轨迹是红色。

## 2. 赛道与"穿过"的判据

```bash
python3 ~/lab4_work/gates.py
```

输出 12 个门（编号 0–11）的位置、朝向和间距，参照 [gate_table.txt](results/logs/gate_table.txt)：

- 门的 yaw 就是穿门方向；
- 门的高度在 2.0–3.6 m 之间；
- 门与门之间直线距离合计 84.4 m，出生点到 0 号门另有 4.8 m。

门在模拟器里只是贴图（`sprite`），**没有碰撞体积**：让无人机从 0 号门旁边 0–2.5 m 的横向偏移处飞过，都没有碰撞记录。数据里也查不到门框尺寸。因此全部分析统一用 [race_check.py](scripts/race_check.py) 的判据：**机体中心依次进入每个门心 0.6 m 以内**。用时定义为从轨迹开始（第一条 `/desired_state`）到首次进入最后一个门的 0.6 m 范围。这一判据和计时口径都是我们自己定的，现场以助教的标准为准。

## 3. Part 0：飞到第一个门悬停

```bash
roslaunch planner_pkg static_point_test.launch
```

- **launch 里启动的节点**：控制器、门位姿发布节点，以及我们实现的 `simple_traj_planner`（[Part 0 代码](planner_pkg/src/simple_traj_planner.cpp)：取第一个门的位姿，速度和加速度置零，发布期望状态并广播 `av-desired` TF）。
- **应该看到的现象**：无人机飞到 0 号门中心 (0.42, 3.17, 2.67)，转向 −90°，悬停在门框里，这个门在模拟器里会变成绿色。
- **检查位置**：`rostopic echo -n1 /current_state/pose/pose/position` 应约为 (0.4226, 3.1652, 2.62)。比目标低的约 5 cm 是增益 kx=8 下的稳态偏差（模拟器里的真实重量比控制器模型约重 3.6%）。参照 [part0_summary.txt](results/logs/part0_summary.txt)。

测完按 **Ctrl-C** 停掉这个 launch，再进行 §4。

## 4. 竞速：用官方 launch 命令（穿过 6 个门、12 个门）

1. **确认没有其他控制器在运行**：Ctrl-C 停掉 §3 或之前的 launch。
2. **停桨并复位**：模拟器会一直执行它收到的最后一条转速指令，所以先发一条全零指令，再在模拟器窗口里按 **R**，然后确认无人机回到了 (0.40, 8.00, ~0.2)：

   ```bash
   rostopic pub -1 /rotor_speed_cmds mav_msgs/Actuators "{angular_velocities: [0, 0, 0, 0]}"
   ```

3. **启动控制器和轨迹生成节点**：无人机此时还停在地面，等待门的位姿。

   ```bash
   roslaunch trajectory_generation traj_following.launch
   ```

4. **（可选）开始录 bag**：

   ```bash
   rosbag record -O ~/lab4_work/race.bag --duration=16 /current_state /desired_state /desired_traj_vertices /rotor_speed_cmds /tesse/collision /tf
   ```

5. **发布门的位姿**：比赛从这一刻开始，约 7 s 跑完全程，之后无人机停在最后一个门后方 6 m 处悬停。

   ```bash
   roslaunch planner_pkg traj_gen.launch
   ```

6. **分析**：

   ```bash
   python3 ~/lab4_work/race_check.py ~/lab4_work/race.bag --plot ~/lab4_work/race.png
   ```

**参照结果**：输出 `gates passed in order: 12/12`，`race time` 约 6.7–6.8 s，最高速度约 17 m/s。起飞离地的瞬间会有 1–3 条 `Floor_01` 接触记录，之后没有碰撞。逐门的偏差参照最快一次 [fastest_run_summary.txt](results/logs/fastest_run_summary.txt)：6.74 s，12 个门的偏差在 0.14–0.55 m 之间。轨迹图见 [Z_c14_r1.png](results/plots/Z_c14_r1.png)。用这套官方 launch 复跑的两次分别是 6.78 s 和 6.80 s。

最终配置写在 [traj_following.launch](trajectory_generation_pkg/launch/traj_following.launch)：

| 参数 | 值 | 作用 |
| --- | --- | --- |
| `time_mode` | 1 | 每段时间按"距离 / 巡航速度"分配，第一段和最后一段（从静止出发、在终点刹停）加倍，消除了 minimum snap 的振铃 |
| `v_max` | 14 | 巡航速度，单位 m/s |
| `exit_distance` | 6 | 终点设在最后一个门后方 6 m，最后一个门可以带速冲过去 |
| `start_factor` | 2 | 起飞段的时间系数 |
| `use_omega_d` | true | 控制器使用轨迹生成节点按微分平坦性算出的期望角速度，做前馈 |
| 增益 | 8/5/10/2 | 和 Lab3 相同 |

**成功率**：这个速度下用最终配置一共飞了 5 次，成功 4 次。失败时一般卡在 0、8 或 9 号门（`DNF`）。失败了就重复第 2–6 步再试；想要更大余量，可以把 launch 里的 `v_max` 改成 12（约 7.9 s）或 10（约 9.4 s），同样保持 `use_omega_d` 为 true。重新比赛之前，先 Ctrl-C 停掉第 3、5 步的两个 launch。

**一键版**：先启动模拟器、roscore 和桥接节点，不要开其他节点，然后运行：

```bash
~/lab4_work/official_run.sh run3
```

脚本会自动完成第 2–6 步，比赛期间录下模拟器画面，比赛结束后截取节点图和话题信息。结果放在 `~/lab4_work/official/run3/`：`race_summary.txt`、`race.png`、`race.bag`、`unity_view.mp4`、`rqt_graph.png`、`ros_communication.txt`。

## 5. ROS 通信（10 分）

比赛结束后，节点仍然在运行，这时执行：

```bash
rosnode info /trajectory_generation_node
rosnode info /controller_node
rostopic hz /desired_state
rqt_graph
```

整条通信链是：

- `/traj_vertices_publisher` → `/desired_traj_vertices`（PoseArray，约 5 Hz）→ `/trajectory_generation_node` → `/desired_state`（约 50 Hz）→ `/controller_node` → `/rotor_speed_cmds` → `/tesse/quadrotor_control_interface`；
- 桥接节点发布的 `/current_state`（50 Hz）同时送到轨迹生成节点和控制器。

参照 [ros_communication.txt](results/logs/ros_communication.txt) 和 [rqt_graph.png](results/screenshots/rqt_graph.png)。如果节点图里出现一排红色的 `/rostopic_xxxx` 节点，那是之前被中途结束的 `rostopic echo` 没来得及注销留下的，先运行 `echo y | rosnode cleanup` 清掉。导出 PNG 的命令是：

```bash
python3 ~/lab4_work/rosgraph_dot.py /tmp/g.dot && dot -Tpng -Gdpi=150 /tmp/g.dot -o ~/lab4_work/rqt_graph.png
```

## 6. 用时与提速：复现优化过程

`run_race.sh` 用 `rosrun` 启动节点，参数全部从命令行和环境变量传入，方便对比实验。它会自动停桨、复位并检查复位成功，然后录 bag、分析，结果追加到 `~/lab4_work/races.txt`，图存到 `~/lab4_work/plots/`。用法是：

```
[环境变量] ~/lab4_work/run_race.sh <名称> <v_max> <a_max> <kx> <kv> <kr> <komega> <录制秒数>
```

环境变量有：`TM`（0 = 模板的时间分配公式，1 = 按距离分配）、`EXIT`（出口距离）、`SF`（起飞段系数）、`OMD=1`（开启 Ω_d 前馈）。运行前先按 §1 启动模拟器、roscore 和桥接节点。

| 阶段 | 命令 | 参照结果 |
| --- | --- | --- |
| 模板默认 | `~/lab4_work/run_race.sh demo_template 8 4 8 5 10 2 35` | 35 s 内只过了 6 个门（规划总时长 67 s，最高速度 3.3 m/s） |
| 按距离分配时间 | `TM=1 ~/lab4_work/run_race.sh demo_c8 8 8 8 5 10 2 30` | 12/12，12.00 s |
| + 出口点、较硬的增益 | `TM=1 EXIT=6 ~/lab4_work/run_race.sh demo_c9 9 8 12 6 20 3 20` | 12/12，10.52 s（约 3/4 成功） |
| + Ω_d 前馈 | `TM=1 EXIT=6 OMD=1 ~/lab4_work/run_race.sh demo_c10 10 8 8 5 10 2 18` | 12/12，9.44 s |
| 12 m/s | `TM=1 EXIT=6 OMD=1 ~/lab4_work/run_race.sh demo_c12 12 8 8 5 10 2 18` | 12/12，7.90 s |
| 14 m/s（最快） | `TM=1 EXIT=6 OMD=1 ~/lab4_work/run_race.sh demo_c14 14 8 8 5 10 2 16` | 12/12，6.74 s（约 2/3 成功） |

- **模板太慢的原因**：模板的时间分配公式（Nfabian）里有个经验常数 6.5，非常保守；单纯调大 v_max 和 a_max，又会让 minimum snap 轨迹上下振铃（高度在 0.9–4.3 m 之间摆）。
- **10 m/s 以上的瓶颈**：控制律忽略了 Ω_d，急弯时姿态滞后约为 komega/kr × 转动角速度，可达 10–17°，无人机会甩向弯道外侧并下坠。加上 Ω_d 前馈后才能飞到 14 m/s。完整分析见 [PLAN.md](PLAN.md) 和 [results/logs](results/logs/)。
- **全部尝试**：55 次尝试统一用同一判据重算后的汇总见 [race_attempts.csv](results/logs/race_attempts.csv)，其中 21 次完整通过。

不起飞、只看规划的命令（读出出生点后生成轨迹，打印总时长、峰值速度和加速度、高度范围），参照 [plan_comparison.txt](results/logs/plan_comparison.txt)：

```bash
EXIT=6 ~/lab4_work/gen_only.sh 14 8 false 500 3 false 1
```

其中 14 m/s 的配置规划时长 7.66 s，峰值速度 16.8 m/s，峰值加速度 36.9 m/s²。另外两个选做的检验脚本是 `thrust_check.py`（结论：模拟器不限制转速和推力）和 `err_profile.py`（1 号门附近的误差剖析），用法都是 `python3 ~/lab4_work/<脚本>.py <bag>`。

## 7. 简答题

### 7.1 简答题 1（25 分）：单段最小速度 QP

```bash
python3 ~/26second-seme/lab4/scripts/d1_qp_check.py
```

参照 [d1_qp_check.txt](results/logs/d1_qp_check.txt)：

- **只有位置约束时**：1、2、3 次多项式的最优解都是 P(t) = t，代价 J = 1。提高次数没有改进，和 Euler-Lagrange 方程的结论一致（最小速度问题的最优轨迹是 2r−1 = 1 次）。
- **加上 P′(1) = −2 之后**：2 次多项式的最优解是 −3t² + 4t，J = 4；3 次多项式的最优解是 −3.75t³ + 4.5t² + 0.25t，J = 2.125。
- **继续提高次数**：代价会降向 1，但永远达不到，因为最小速度代价不允许在端点固定速度。

在 Mac 或 Ubuntu 上都能运行，只需要 numpy。

### 7.2 简答题 2（25 分）：多段 minimum snap 的约束计数

```bash
python3 ~/26second-seme/lab4/scripts/d2_constraint_count.py
```

脚本会真的搭出约束矩阵，验证 r = 2–5、k = 1–5 的所有组合下，约束数都等于未知数 2rk，且矩阵满秩。minimum snap（r = 4）的计数是：

| 约束类型 | 数量 |
| --- | --- |
| 路点约束 | 2k |
| 中间点的导数连续约束（自由导数） | 6(k−1) |
| 起点和终点的固定导数约束 | 6 |
| 合计 | 8k |

参照 [d2_constraint_count.txt](results/logs/d2_constraint_count.txt)。

## 8. 视频与 rosbag

- **模拟器视角**：`official_run.sh` 会自动录，见 [unity_view_official_6.78s.mp4](results/video/unity_view_official_6.78s.mp4)。手动录可以用 Windows 的 Xbox Game Bar（Win+Alt+R）或 OBS。
- **在 rviz 里回放最快那次**：在桥接节点的终端按 Ctrl-C 停掉桥接，否则实时数据会和回放数据混在一起；再重启 rviz，清掉旧轨迹，然后播放：

  ```bash
  rviz -d ~/lab4_work/lab4_topview.rviz
  rosbag play --clock -d 1 ~/26second-seme/lab4/results/bags/fastest_run_6.74s.bag
  ```

  播放时用 Game Bar 录屏，或者用 Lab3 说明书 §8 的按窗口抓帧命令（窗口名改成 `lab4_topview.rviz`）。参照 [rviz_fastest_6.74s_replay.mp4](results/video/rviz_fastest_6.74s_replay.mp4)。回放完记得重新启动桥接节点。

## 9. 常见问题

| 现象 | 原因与处理 |
| --- | --- |
| 模拟器一启动就退出，Player.log 里有 `xcb` 报错 | 没加 `-force-gfx-direct` |
| 收不到 `/current_state`，桥接日志里有 `AssertionError` | 没打 `patch_bridge.py`（Lab3 说明书 §1.2）；打过修补就重启桥接 |
| rviz 里看不到门，PoseArray 报 Error | 没运行 `gate_relay.py`，或 rviz 没订阅 `/gates_world` |
| 复位后无人机被推着乱飞 | 没先发全零转速指令（§4 第 2 步） |
| 节点图里有一排红色的 `/rostopic_xxxx` | 运行 `echo y | rosnode cleanup` |
| 编译报 `does not match the source ... used to generate cache` | 包换了位置后的旧缓存，删除 `build/<包>` 和 `devel/.private/<包>` 后重新编译 |
| 编译报重名的包 | `src/` 下同时有 `catkin_simple` 或 `mav_comm` 和 `dependencies/` 里的副本 |
| 竞速失败（DNF） | 这个速度下成功率约 4/5。复位后重试，或把 `v_max` 降到 12 |
