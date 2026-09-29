# Lab2 实施方案：ROS、双无人机 TF 与轨迹分析

规划日期：2026-09-23，复核日期：2026-09-24。建议采用 **Ubuntu 20.04 + ROS Noetic + 官方 `VNAV2023` 代码**，按“环境 → 静态场景 → 动态 TF → 相对轨迹 → 数学证明 → 报告与现场检查”的顺序完成。

状态：实验与英文 PDF 报告已完成，现场检查及正式提交待按助教通知进行。得分点 1–5（ROS 安装、双机运动、轨迹、数学推导、四元数性质）已在远程 x86-64 主机的 WSL 2 Ubuntu 20.04.6 + ROS Noetic 中完成；代码见 [two_drones_pkg](two_drones_pkg/)，实测记录见 [results/logs](results/logs/) 和 [results/screenshots](results/screenshots/)，数值校验脚本见 [scripts](scripts/)。报告见 [lab2_report.pdf](report/lab2_report.pdf)。下文保留规划时的原文，其中“待完成”等说法以本状态行为准。

## 1. 任务范围与交付物

依据 [本课程说明](../syllabus.md)、[Lab2 课件](Lab2.pdf) 和指定的 [MIT 2023 Lab2 题目](https://vnav.mit.edu/labs_2023/lab2/exercises.html)：

| 工作包 | 要完成的工作 | 应保留的交付物与证据 |
| --- | --- | --- |
| A. ROS 安装 | 配置 Noetic，启动 ROS，运行并操控小海龟 | 系统/ROS 版本记录、小海龟运行图、节点和话题记录 |
| B. ROS 基础与双机运动 | 分析静态 launch；补全 TF 发布节点，让两架无人机按指定位置和姿态运动 | 基础问答、完整 ROS 包、静态/动态图、TF 树 |
| C. 轨迹与参考系 | 补全变换查询，在 RViz 中显示三条轨迹，切换 `world` 和 `av1` | 三轨迹截图、参考系对照图、变换方向解释 |
| D. 数学推导 | 完成抛物线、相对位置、轨迹平面、平面坐标、椭圆半轴五问 | 带齐次矩阵和中间步骤的排版推导 |
| E. 四元数性质 | 证明两种乘法矩阵的正交性、单位元关系和交换关系 | 统一约定的证明、可选数值自检 |
| F. 提交与检查 | 整理实验报告，重跑演示并准备解释 | 报告 PDF 及源文件、代码、运行说明、真实结果和问题分析 |

MIT 的节点/话题/launch 四个问题也要完成，不能只让两架无人机“看起来在动”。本课程明确要求现场检查，报告不能代替检查。

### 开始时记录并向助教核实的事项

这些事项影响最终验收口径，但不妨碍先完成 A—E 的明确任务：

1. **运动控制范围：** 课件 PDF 第 16 页（页脚 15/21）提到 `Twist`、Gazebo 或硬件运动执行；课件的核心目标和 MIT 2023 则是通过 TF 展示规定的运动。当前方案以完整 MIT 双机任务为主线。若助教另要求速度/姿态控制，需要明确指定模拟器、机器人模型、指令话题及验收动作，再增加控制节点；不能把 RViz 模型运动写成真实动力学控制成果。
2. **分值：** 本课程列出 20、40、30、10、10，合计 110；MIT 原题的分配不同。先覆盖所有任务，分数换算按助教答复记录，不自行改成 100 分。
3. **日期：** [教学日历](../calendar.md) 同时列出 10 月 9 日和 10 月 23 日检查 Lab1/Lab2；[课程说明](../syllabus.md) 对 Lab2 写一周、通用规则又写两周。下面是一周工作安排，不代表正式截止日期，优先核实最近检查及线上提交时间。
4. **Notion 补充说明：** [课程链接](https://spurious-cornflower-507.notion.site/Lab2-ROS-105e9f90e72480519605ed793e6662dc) 本次未能读取，不能确认其中是否有额外要求；拿到可访问内容后对照补充。

## 2. 固定环境和代码版本

默认沿用 Lab1 的 Ubuntu 20.04；若尚未准备好，先完成环境验收再开始写节点。[MIT 2023 安装页](https://vnav.mit.edu/labs_2023/lab2/ros.html) 也指定 Ubuntu 20.04 与 Noetic。

| 项目 | 本方案选择 | 原因 |
| --- | --- | --- |
| 操作系统 | Ubuntu 20.04，优先复用已有 Lab1 环境 | 与课程示例匹配 |
| ROS | ROS1 Noetic | 对应 `roscore`、`roslaunch`、catkin、`ros::` API |
| 上游版本 | `VNAV2023` 标签 | 官方标注为最后一版 ROS1 课程代码 |
| 固定提交 | `7d234d8b3618f0090b61fc6551f3e582db116f9c` | 便于复现实验与定位差异 |
| 编译工具 | `catkin build`，C++11 | 沿用官方包的构建方式 |
| 可视化 | RViz、`rqt_graph` | 查看网格、轨迹、节点及话题 |

**版本选择很关键：** 当前上游 `main` 的 Lab2 已使用 ROS2；直接下载主分支会与课程里的 ROS1 命令不匹配。获取 [官方 VNAV2023 发布版](https://github.com/MIT-SPARK/VNAV-labs/releases/tag/VNAV2023)，不要在开始实验后用无约束的 `git pull` 切回新版。

Noetic 已于 2025-05-31 结束官方维护；本实验继续采用它是为了复现课程接口。安装成功后记录软件版本并保留环境快照。[ROS 官方说明](https://www.ros.org/blog/noetic-eol/)

如果使用 Mac，先落实能显示 RViz 的 Ubuntu 环境，并核对处理器架构和镜像。第一天就验证图形窗口；本方案中的 Linux 命令应在 Ubuntu 终端运行。

### 环境完成条件

- `lsb_release -a`、`uname -m`、`rosversion -d` 的输出已保存。
- 每个终端均加载 `/opt/ros/noetic/setup.bash`；构建后再加载工作区的 `devel/setup.bash`。
- `roscore` 可运行，`turtlesim_node` 和 `turtle_teleop_key` 可启动，键盘能控制海龟。
- `catkin build` 可用，RViz 正常显示场景。

三个终端分别验证：

```bash
# 终端 1
source /opt/ros/noetic/setup.bash
roscore

# 终端 2
source /opt/ros/noetic/setup.bash
rosrun turtlesim turtlesim_node

# 终端 3：按方向键前保持此终端获得键盘焦点
source /opt/ros/noetic/setup.bash
rosrun turtlesim turtle_teleop_key
```

安装工具包括 `python3-catkin-tools`、`python3-rosdep` 和编译工具；ROS 安装源和签名配置需按实际 Ubuntu 环境核验。`rosdep init` 仅在未初始化时执行；Noetic 属于 EOL 发行版，更新依赖索引时使用 `rosdep update --include-eol-distros`。[rosdep 官方维护者说明](https://discourse.ros.org/t/rosdep-and-eol-distros/7640)

## 3. 工作区与文件安排

建议把自己修改的完整包保存在课程仓库，用符号链接接入 `~/vnav_ws/src/`。这样只维护一份源码，构建产物留在工作区。

以下为首次准备的示例命令，**尚未执行**。在 Ubuntu 上的本课程仓库根目录运行，前提是目标目录尚未存在；已有目录时先检查内容并复用，不覆盖已有工作。

```bash
lab_repo_dir="$(git rev-parse --show-toplevel)"
git clone --branch VNAV2023 --depth 1 \
  https://github.com/MIT-SPARK/VNAV-labs.git "$HOME/VNAV-labs-upstream"
git -C "$HOME/VNAV-labs-upstream" rev-parse HEAD
# 核对输出为 7d234d8b3618f0090b61fc6551f3e582db116f9c

cp -a "$HOME/VNAV-labs-upstream/lab2/two_drones_pkg" "$lab_repo_dir/lab2/"
mkdir -p "$HOME/vnav_ws/src"
ln -s "$lab_repo_dir/lab2/two_drones_pkg" "$HOME/vnav_ws/src/two_drones_pkg"
```

复制完成后，先修正 `plots_publisher_node.cpp` 的成员声明顺序，再首次编译。应先声明 buffer，再声明使用它的 listener：

```cpp
tf2_ros::Buffer tf_buffer;
tf2_ros::TransformListener tf_listener;
```

原模板顺序相反，而构造函数使用 `tf_listener(tf_buffer)`。C++ 按成员声明顺序初始化，只调整初始化列表顺序无效。此修正应在静态场景首次启动前完成。[原模板源码](https://github.com/MIT-SPARK/VNAV-labs/blob/7d234d8b3618f0090b61fc6551f3e582db116f9c/lab2/two_drones_pkg/src/plots_publisher_node.cpp)

```bash
source /opt/ros/noetic/setup.bash
cd "$HOME/vnav_ws"
catkin init
rosdep update --include-eol-distros
rosdep install --from-paths src --ignore-src --rosdistro noetic -y
catkin build
source devel/setup.bash
```

建议最终组织如下；本次只创建计划文件，不预先生成空报告或实验结果：

```text
lab2/
  README.md
  Lab2.pdf
  PLAN.md
  two_drones_pkg/             # 保留完整包、launch、config、mesh 和源文件
  notes/
    environment.md           # Ubuntu/ROS/编译器版本、上游提交、运行命令
    ros_questions.md         # 基础问答、节点与话题表
    derivations.md           # 数学与四元数证明；也可用 .tex
  results/
    screenshots/             # 实际运行截图
    logs/                    # 编译、节点、话题、TF 查询记录
    trajectory_samples.csv   # 可选：同一时刻的理论值与 TF 结果
  report/
    lab2_report.tex           # 或其他规范排版源文件
    lab2_report.pdf
```

记录上游来源并保留原包的版权/许可证声明。`build/`、`devel/` 和临时日志不作为源码提交；结果目录只收集与报告结论有关的材料。

## 4. 分阶段实施与验收

### 阶段 A：理解静态场景

启动：

```bash
source /opt/ros/noetic/setup.bash
source "$HOME/vnav_ws/devel/setup.bash"
roslaunch two_drones_pkg two_drones.launch static:=True
```

结合 [固定版本 launch 文件](https://github.com/MIT-SPARK/VNAV-labs/blob/7d234d8b3618f0090b61fc6551f3e582db116f9c/lab2/two_drones_pkg/launch/two_drones.launch) 和实际运行输出完成：

| 模式 | 主要节点 | 主要职责 |
| --- | --- | --- |
| 静态 | `/av1broadcaster`、`/av2broadcaster` | 向 `/tf_static` 发布 `world` 到两机的固定关系 |
| 动态 | `/frames_publisher_node` | 向 `/tf` 发布两机随时间变化的位姿 |
| 两种模式共有 | `/plots_publisher_node` | 订阅 TF，向 `/visuals` 发布无人机网格和轨迹的 `MarkerArray` |
| 两种模式共有 | `/rviz` | 根据 TF 和 `/visuals` 显示场景 |

用 `rosnode list`、`rosnode info`、`rostopic list`、`rostopic info /visuals` 和 `rqt_graph` 保存实际关系。上表省略 `/rosout` 等辅助节点；完整记录以运行情况为准。

应能够解释四件事：有哪些节点；各自发布/订阅什么；如何用 `roscore` 和多个 `rosrun` 复现 launch；省略 `static:=True` 后 `if/unless` 如何切换发布节点。动态 TODO 尚未实现时，省略参数会启用未完成的发布节点，缺少两机 TF，绘图节点可能一直等待，这是需要解释的现象。

静态手动启动时，在不同终端执行以下命令，每个终端先加载 ROS 和工作区环境；先停止原 launch，避免重复节点和 TF 发布者：

```bash
roscore
rosrun tf2_ros static_transform_publisher 1 0 0 0 0 0 1 world av1 __name:=av1broadcaster
rosrun tf2_ros static_transform_publisher 0 0 1 0 0 0 1 world av2 __name:=av2broadcaster
rosrun two_drones_pkg plots_publisher_node
rosrun rviz rviz -d "$(rospack find two_drones_pkg)/config/default.rviz"
```

**验收：** 两机静止；AV1 位于 `(1,0,0)`，AV2 位于 `(0,0,1)`；RViz 能显示 TF 坐标轴与无人机网格。此时轨迹查询尚未补全，不把模板产生的轨迹当成正确结果。

### 阶段 B：补全动态 TF 发布

主要修改 [frames_publisher_node.cpp](https://github.com/MIT-SPARK/VNAV-labs/blob/7d234d8b3618f0090b61fc6551f3e582db116f9c/lab2/two_drones_pkg/src/frames_publisher_node.cpp)。

任务拆分：

1. 在类中持有 `tf2_ros::TransformBroadcaster`。
2. 每次回调只读取一次 `now`，计算 `t = (now - startup_time).toSec()`；不要把 Unix 时间戳直接作为题目中的 `t`。
3. 两个 `TransformStamped` 使用同一时间戳，父坐标系均为 `world`，子坐标系分别为 `av1`、`av2`。
4. AV1 平移设置为 `(cos(t), sin(t), 0)`，姿态设置为 `setRPY(0,0,t)`。
5. AV2 平移设置为 `(sin(t), 0, cos(2*t))`，姿态采用单位四元数 `(0,0,0,1)`。
6. 在模板的 0.02 秒定时回调内广播两组变换，目标频率 50 Hz。

特别注意：题目规定 **AV1 的 y 轴沿运动切线**。`yaw=t` 已满足这一条件，不应为了让 x 轴朝前而再加 `π/2`。ROS 四元数消息按 `x,y,z,w` 分量赋值。

重新编译并启动动态场景：

```bash
cd "$HOME/vnav_ws"
catkin build
source devel/setup.bash
roslaunch two_drones_pkg two_drones.launch
```

**验收：** AV1 在 `xy` 平面沿单位圆运动；AV2 在 `xz` 平面沿抛物线段往返；AV1 的 y 轴沿切线、z 轴与世界 z 轴平行；AV2 的坐标轴保持与世界坐标轴平行。

### 阶段 C：补全相对变换和三条轨迹

主要修改 [plots_publisher_node.cpp](https://github.com/MIT-SPARK/VNAV-labs/blob/7d234d8b3618f0090b61fc6551f3e582db116f9c/lab2/two_drones_pkg/src/plots_publisher_node.cpp) 中 `TrajTrail::update()` 的 TODO：

```cpp
transform = parent->tf_buffer.lookupTransform(
    ref_frame, dest_frame, ros::Time(0));
```

此 API 顺序是 **目标参考系、源坐标系、时间**：将 `dest_frame` 中的坐标表示到 `ref_frame`，也就是查询运动物体相对指定参考系的位姿。相对轨迹应查询 `("av1", "av2", ros::Time(0))`；时间 0 表示最新可用变换。[ROS 官方 Buffer 定义](https://github.com/ros/geometry2/blob/noetic-devel/tf2_ros/include/tf2_ros/buffer.h)

同时检查启动和查询的异常处理：

- 确认第 3 节的 buffer/listener 声明顺序修正已经生效。
- 启动时等待 TF 的循环增加短暂休眠和有节制的日志，避免无变换时忙等占满 CPU；等待过久时报告缺失的 frame。
- 保留模板的异常捕获。查询失败时跳过本次样本，不能把默认零变换加入轨迹。

保留原有 Marker 输出，最终展示：

| 轨迹 | 参考系 | 预期形状 |
| --- | --- | --- |
| AV1，蓝色实线 | `world` | 单位圆 |
| AV2，红色实线 | `world` | 抛物线段 |
| AV2，红色虚线 | `av1` | 位于斜平面内的椭圆 |

分别保存 Fixed Frame=`world` 和 Fixed Frame=`av1` 的截图。相对轨迹 Marker 的 `frame_id` 必须为 `av1`；世界轨迹则为 `world`。`world` 视角里，相对轨迹随 AV1 坐标系一起运动是正常的。

模板世界轨迹保留 300 个点，名义 50 Hz 下约为 6 秒，小于 `2π` 秒的世界运动周期；如果希望截图显示完整圆，可将世界轨迹缓冲增加到 400 点并运行至少 8 秒。相对轨迹 160 点约为 3.2 秒，覆盖其 `π` 秒周期；实际还应观察丢帧和采样间隔，不能仅凭点数断言采样完整。

**验收：** 三条曲线均可见；切换参考系后运动关系正确；持续运行时没有持续的 TF 查询错误。

## 5. 数学部分的推导路线与校验值

统一记号：`T^A_B` 表示 B 坐标系相对 A 的位姿，并把 B 中的齐次坐标变换到 A：`p^A = T^A_B p^B`。课件 PDF 第 12—13 页的箭头记号容易产生歧义，报告用这一约定贯穿全部推导。

设 `c=cos(t)`，`s=sin(t)`。先写出 `T^w_1` 和 `T^w_2`，再计算 `T^1_2=(T^w_1)^(-1)T^w_2`：

$$
T^w_1=\begin{bmatrix}c&-s&0&c\\s&c&0&s\\0&0&1&0\\0&0&0&1\end{bmatrix},\qquad
T^w_2=\begin{bmatrix}1&0&0&s\\0&1&0&0\\0&0&1&\cos 2t\\0&0&0&1\end{bmatrix}.
$$

五问按下列路线展开，报告应保留求逆、相乘、消元和换基步骤：

| 问题 | 关键思路 | 理论校验值 |
| --- | --- | --- |
| AV2 为什么是抛物线段 | 消去参数 `t` | `y=0, z=1-2x², -1≤x≤1` |
| AV2 相对 AV1 的位置 | `Rz(t)^T (p2w-p1w)` | `(sc-1, -s², cos(2t))` |
| 相对轨迹在哪个平面 | 找 y、z 的线性关系 | `z-2y=1` |
| 平面内的居中坐标系 | 原点取 `(-1,-1/2,0)`；选择单位正交基 | `ex=(1,0,0)`，`ey=(0,1,2)/√5`，`ez=(0,-2,1)/√5` |
| 是否为椭圆、半轴多长 | 将相对位置减去平面原点，再投影到上述基 | `xp=(1/2)sin(2t)`，`yp=(√5/2)cos(2t)`，`zp=0`；半轴 `1/2`、`√5/2` |

相对完整变换应为：

$$
T^1_2=\begin{bmatrix}
c&s&0&sc-1\\-s&c&0&-s^2\\0&0&1&\cos 2t\\0&0&0&1
\end{bmatrix}.
$$

由平面基构造 `R^1_p=[ex ey ez]` 和 `T^1_p`，再用 `(T^1_p)^(-1)` 求平面坐标，最后得到：

$$
\frac{x_p^2}{1/4}+\frac{y_p^2}{5/4}=1.
$$

相对位置的周期是 `π`；包含姿态的完整相对位姿周期是 `2π`，二者要区分。

相对位置的三个简单检查点：

| `t` | `p2^1(t)` |
| --- | --- |
| `0` | `(-1,0,1)` |
| `π/4` | `(-1/2,-1/2,0)` |
| `π/2` | `(-1,-1,-1)` |

这些值用于发现参考系写反、姿态差 `π/2`、平移直接相减而漏乘旋转等错误；它们不代表已经取得的 ROS 数据。动态采样需比较相同时间的值，不能用 RViz 截图时刻或另一个节点的启动时刻代替 TF 对应的 `t`。

## 6. 四元数证明安排与课件勘误

按 `q=(v,w)=(q1,q2,q3,q4)`、标量在最后，定义 `[v]×a=v×a`。采用 MIT 原题中的分块形式：

$$
\Omega_1(q)=\begin{bmatrix}wI+[v]_\times&v\\-v^T&w\end{bmatrix},\qquad
\Omega_2(q)=\begin{bmatrix}wI-[v]_\times&v\\-v^T&w\end{bmatrix}.
$$

**课件勘误：** PDF 第 19 页（页脚 18/21）的 `Ω1` 第 `(1,3)` 项写为 `-q2`，第 `(2,3)` 项写为 `+q1`；[MIT 原题](https://vnav.mit.edu/labs_2023/lab2/exercises.html) 对应为 `+q2` 和 `-q1`。本次已核对 PDF 图像；证明按与四元数左乘一致的 MIT 版本进行，并在报告注明差异。

证明顺序：

1. 用 `[v]×^T=-[v]×` 和 `[v]×²=vv^T-||v||²I`，先推出 `Ωi(q)^TΩi(q)=||q||²I4`；单位四元数时等于 `I4`。解释为左右乘单位四元数保持任意四元数的范数。
2. 令单位元 `e4=(0,0,0,1)^T`，由 `Ωi(q)e4=q` 和正交性得 `Ωi(q)^Tq=e4`。
3. 用四元数乘法结合律证明左乘与右乘交换；再用 `Ω2(y)^T=Ω2(conj(y))` 证明带转置的关系。此题的 `x,y` 是任意四维向量，不应额外假定它们为单位四元数。

可用随机样本数值检查符号，但数值验证不能代替证明。MIT 的内禀/外禀旋转题明确为可选题，完成本课程五项要求后再考虑。

## 7. 验证、证据与报告

建议在写代码时同步收集证据：

| 验证内容 | 方法 | 通过标准 |
| --- | --- | --- |
| 环境 | 版本命令、小海龟键盘操作 | 版本匹配，通信与图形界面可用 |
| 静态 TF | 节点/话题查询、RViz TF | `world` 下有 `av1`、`av2`，位置正确 |
| 动态发布 | `/tf` 消息和逐 frame 频率检查 | 时间戳持续更新，每个 frame 名义 50 Hz，两个子坐标系无重复发布者 |
| 旋转 | 四元数范数、RViz 坐标轴 | 单位范数，AV1 y 轴沿切线 |
| 相对变换 | 同时刻矩阵计算与 TF 查询对照 | 方向一致；记录时间对齐方式和实际残差 |
| 几何关系 | 检查 `x1²+y1²-1`、`z2-1+2x2²`、`zrel-2yrel-1` | 理论计算残差接近浮点精度，ROS 采样偏差可解释 |
| 轨迹显示 | 两种 Fixed Frame、足够长的采样 | 三条曲线完整可辨，Marker 参考系正确 |
| 重跑 | 新终端加载环境后编译、启动 | 不依赖编辑器终端中的残留环境变量 |

两条 TF 每次合并为一条消息发送时，`/tf` 总消息频率约 50 Hz；分开发送时可约为 100 Hz。不能仅凭总话题频率判断单个 frame 是否按 50 Hz 更新。

对解析公式和矩阵运算的离线 double 自检，可采用 `1e-9` 量级容差；这只是自检建议，不是课程评分阈值。ROS 的在线比较要考虑时间对齐、插值和采样频率，单独报告实际误差。

报告建议依次写：实验目的；环境与代码版本；节点及话题关系；两个节点的实现思路；世界/相对轨迹结果；五问数学推导；四元数证明；问题处理与个人分析；复现命令。突出“为什么这样做”，包括变换方向、时间戳、四元数顺序和参考系改变的影响。

现场演示可准备约 5 分钟流程：小海龟 → 静态双机 → 动态双机及三轨迹 → Fixed Frame 切换 → 用齐次变换解释椭圆。准备回答 TF 与运动控制的区别、为什么 AV1 使用 `yaw=t`、为什么不能只减去两个位置。

## 8. 一周执行安排

以下工时是基于已具备 Lab1 基础的规划估计，合计约 16—21 小时；新建虚拟机或修复安装问题另留缓冲。各阶段达到验收条件后再进入下一阶段。

| 天 | 工作 | 估计投入 | 当天完成标志 |
| --- | --- | --- | --- |
| D1 | 核实任务口径，准备 Noetic、小海龟、RViz，获取固定版本 | 3—4 小时 | 环境记录与小海龟证据齐全 |
| D2 | 编译模板、静态场景、节点话题与 launch 问答 | 2 小时 | 可手动复现场景并解释通信关系 |
| D3 | 完成动态 TF 发布、检查位置和姿态 | 3—4 小时 | 两机按题设运动，无持续 TF 错误 |
| D4 | 完成查询、三轨迹、参考系切换及数值对照 | 2—3 小时 | 圆、抛物线和相对椭圆均可验证 |
| D5 | 五问数学推导与四元数证明 | 3—4 小时 | 推导完整，符号和代码约定一致 |
| D6 | 整理报告、截图、版本和复现命令 | 2—3 小时 | 形成可提交报告与完整代码包 |
| D7 | 新终端重跑、现场演示彩排、检查遗漏 | 1 小时 | 可独立运行并解释所有必做部分 |

若多人协作，可把环境/证据、节点/联调、推导/核验分开并行；D4 集成一次，D6 互相复查。每个人都要能解释代码和推导，个人总结按自己的实际过程撰写。单人执行直接依上表顺序推进。

## 9. 完成清单

- [ ] 已确认实际运行环境、验收范围和截止日期。
- [ ] ROS、小海龟、RViz 运行成功，环境信息已留档。
- [ ] 使用 `VNAV2023` 对应提交，完整包和资源文件齐全。
- [ ] 节点/话题/launch 四问完成，并用运行结果核对。
- [ ] 动态发布的时间、父子坐标系、平移与旋转符合题设。
- [ ] TF 查询方向正确，模板 buffer/listener 声明顺序已修正。
- [ ] 三条轨迹和两种 Fixed Frame 的真实截图齐全。
- [ ] 数学五问写出齐次矩阵、中间过程、平面与椭圆半轴。
- [ ] 四元数三组性质证明完整，课件符号差异已说明。
- [ ] 报告写明真实问题、解决办法和个人思考。
- [ ] 从新终端可重现结果，已准备现场检查。
- [ ] 提交物没有把理论预期、模板输出或未执行步骤标成实测结果。
