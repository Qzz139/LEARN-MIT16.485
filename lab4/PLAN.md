# Lab4 实施方案：轨迹优化与无人机竞速

规划日期：2026-10-13。分工、环境、进度、现场演示和风险是 Lab3 和 Lab4 共用的，见 [lab3/PLAN.md](../lab3/PLAN.md)。本文件只写 Lab4 自己的任务。

**状态（2026-10-14）**：实验部分已完成，报告待写。

- **最快成绩**：12/12 门，**6.74 s**（MIT 纪录 10.3 s）。用官方 launch 复跑两次，分别为 6.78 s 和 6.80 s。最终配置写在 [traj_following.launch](trajectory_generation_pkg/launch/traj_following.launch)。
- **关键改动**：
  - 时间分配按距离计算，第一段和最后一段（从静止出发、在终点刹停）加倍，消除了 minimum snap 的振铃；
  - 在最后一个门后加出口点，让最后一个门带速通过；
  - 加入 Ω_d 前馈：轨迹生成节点按微分平坦性算出期望角速度，控制器通过 `use_omega_d` 开关使用它。这项改到了 Lab3 的控制器，但开关默认关闭，Lab3 的行为不受影响；
  - 期望状态的发布频率从 5 Hz 提到 50 Hz。
- **尝试过但放弃的方案**：轨迹库的非线性时间优化（软约束压不住加速度，优化器也提前停止）；逐段按峰值加速度缩放时间（迭代发散）；单独放慢急弯路段；缩短起飞段。
- **证据**：见 [results](results/)，包括全部 55 次尝试的汇总表、最快一次的 rosbag、rviz 回放视频、模拟器视角视频、节点图和逐门偏差表。
- **环境处理**：见 [environment.txt](results/logs/environment.txt)。模拟器需加 `-force-gfx-direct` 参数；修补了桥接节点在时钟倒退时的断言；门框是贴图，没有碰撞体积，因此用"距门心 0.6 m 以内"作为穿门判据。

下文保留规划时的原文。

依据：[课程说明](../syllabus.md) 的给分点，以及 README 指定的 [MIT 2023 Lab4 题目](https://vnav.mit.edu/labs_2023/lab4/exercises.html)。代码使用 `VNAV2023` 标签。

## 0. 已核实与已定（2026-10-13）

- **环境**：Lab4 的 20 个包已在 `~/vnav_ws` 全部编译通过。编译前删除了 Lab3 阶段放进来的 `catkin_simple` 和 `mav_comm`，因为 `dependencies/` 里各自带了一份；那两个包的旧编译缓存也一并清掉了。
- **门的数量**：模拟器数据 `vnav-2020-lab4_static_tfs.csv` 里有 `red_square_drone_door` 编号 0–11，**正好 12 个门**，和课程给分点一致。
- **决定 1（用户）**：**尽力冲用时排名**，但 12 个门必须全部穿过。
- **决定 2（用户）**：控制器增益先用 Lab3 最终的 (8, 5, 10, 2)；撞门或跟不上时再为 Lab4 单独调参，仍然同时看跟踪误差和平滑度。Lab3 报告保留它自己的增益。
- **过门判定**：门框尺寸不在数据里，所以打开桥接节点的碰撞上报（`publish_collisions`），以"全程无碰撞，且轨迹依次穿过每个门所在的平面"作为证据。
- **沿用 Lab3 的教训**：每次实验除了用时，还要记录平滑度指标（转速是否频繁反转、姿态抖动）；误差分析用带时间戳的期望位姿对齐。

## 1. 前置条件

- Lab3 的控制器已经能稳定跟圆。
- 把 Lab3 调好的增益（kx / kv / kr / komega）复制到 `static_point_test.launch` 和 `traj_following.launch`。赛道比圆轨迹更激进，增益可能要重新调。
- 编译 `dependencies/`（mav_trajectory_generation、nlopt、glog 等）。编译时可能缺少系统库，Claude 列出清单后由用户执行 `sudo apt install`。删除 Lab3 阶段克隆的 `mav_comm`，因为 `dependencies/` 里已经自带一份。

## 2. 任务与证据

| # | 给分点 | 做法 | 报告证据 |
| --- | --- | --- | --- |
| 4.1 | 简答题 1（25 分）：单段最小速度 QP | 对 1、2、3 次多项式分别写出 Q、A、b 并求解，和 Euler-Lagrange 结论对照；再加约束 P′(1) = −2 求解 | 手推结果，加 Python 数值验证脚本和输出 |
| 4.2 | 简答题 2（25 分）：多段 minimum snap 的约束计数 | 每段是 7 次多项式，共 8k 个未知数；分别数出路点约束、固定导数约束和自由导数约束；再推广到最小化 r 阶导数的情况 | 推导过程和 k=3 的示意 |
| 4.3 | ROS 通信（10 分） | `traj_vertices_publisher` 从模拟器数据里的 csv 读出门的位姿，发布到 `/desired_traj_vertices`；轨迹生成节点订阅它，并发布 `/desired_state` | `rqt_graph`、`rostopic echo -n1 /desired_traj_vertices` |
| 4.4 | 穿过 1 个门（10 分） | Part 0（`simple_traj_planner.cpp`）：先飞到第一个门并悬停，这一步作为热身；然后跑完整轨迹，记录穿过第 1 个门 | 悬停截图、过门截图 |
| 4.5 | 穿过 6 个门（10 分） | Part 1.1–1.3（`trajectory_generation_node.cpp`）：1.1 填当前位置；1.2 设 D=3，按门位置和 yaw 设置顶点约束（注意 yaw 在 2π 处回绕，终点用 `makeStartOrEnd`）；1.3 设置采样时间，按时间采样轨迹并发布 | rviz 截图 |
| 4.6 | 穿过 12 个门（20 分） | 跑完整条赛道 | rviz 俯视图（期望和实际轨迹叠加门的位置）、完整录屏、`rosbag record /current_state /desired_state` |
| 4.7 | 用时排名加分（10/8/6/4/2 分） | 调整 `v_max` / `a_max`（默认 8 m/s、4 m/s²）、各段时间分配和控制器增益。每次尝试都要确认 12 个门全部穿过 | 每次尝试的参数、用时和是否完赛的表格；最快一次的 rosbag |

## 3. 需要核实的事项

1. **门的数量。** 课程按 12 个门给分，但实际数量要看模拟器 csv 里有几个门。`traj_vertices_publisher` 启动时会打印 `Finished loading trajectory csv: N`，用这个 N 确认是否为 12。
2. **用时的口径。** MIT 没有写清楚怎么计时。本方案定义为：从 `/desired_state` 开始变化，到无人机穿过最后一个门为止，时间从 rosbag 里取。报告中写明这个口径；如果助教有统一的计时方法，以助教为准。
3. **如何判定“穿过”。** 用 rosbag 里的实际位置，检查轨迹是否从门框内部穿过门所在的平面，比肉眼看录屏可靠。
