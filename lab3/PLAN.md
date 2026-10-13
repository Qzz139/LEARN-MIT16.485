# Lab3 实施方案：几何控制器与圆轨迹跟踪

规划日期：2026-10-13。

**状态（2026-10-13）**：实验部分已完成，报告待写。控制器见 [controller_pkg](controller_pkg/)，最终增益为 kx=8、kv=5、kr=10、komega=2：绕圈位置误差 RMS 4.3 cm，俯仰抖动 0.26°。第一轮调参只看跟踪误差，选出的 (20, 7, 30, 4) 精度更高，但有高频颤振，螺旋桨频繁反转，因此按"误差 + 平滑度"重新选了参数。证据在 [results](results/)，分析脚本在 [scripts](scripts/)。环境上做过的处理：桥接节点两个脚本的首行改为 `python3`；复位改用 `xdotool key --window`；录屏改为按窗口抓帧。下文保留规划时的原文。

Lab3 和 Lab4 在 **10/23 一起现场检查**（[教学日历](../calendar.md)），而且 Lab4 要用 Lab3 的控制器。所以两份实验的共用部分（分工、环境、进度、演示）都写在本文件里，Lab4 自己的任务见 [lab4/PLAN.md](../lab4/PLAN.md)。

依据：[课程说明](../syllabus.md) 的给分点，以及 README 指定的 [MIT 2023 Lab3 题目](https://vnav.mit.edu/labs_2023/lab3/exercises.html)。

## 1. 分工与已定事项

团队只有两个成员：用户和 Claude。

| 角色 | 负责 |
| --- | --- |
| 用户 | 所有 `sudo` 操作（Claude 不代输密码）、Windows 桌面上的操作、和助教沟通、审稿、给“个人思考”写大纲、10/23 现场演示 |
| Claude | 通过 SSH 在 WSL 里写代码、编译、运行、调参，留存截图和数据，起草报告 |

| 事项 | 决定 |
| --- | --- |
| 现场演示 | 用户带 Mac，在实验室用 Moonlight/SSH 远程连接家里的 Windows 主机运行 |
| 个人思考（占 35%） | 用户给大纲，双方交流细节后共同完成 |
| 报告 | Lab3、Lab4 各写一份英文 tufte 风格的 PDF |
| 代码版本 | **`VNAV2023` 标签**（偏离 README，原因见下） |

**代码版本说明：** README 链接的是 `VNAV2021` 版本。和 `VNAV2023` 对比后发现，lab3/lab4 的差别只有 4 处：

1. `traj_publisher` 从 tf 迁移到了 tf2；
2. `requirements.txt` 增加了 `scipy`；
3. Lab4 的 launch 文件里，模拟器路径从 `vnav-2021-lab4/` 改成了 `lab4/`；
4. Lab4 的 launch 文件里预留了控制器增益参数。

现在能下载到的模拟器（`vnav.mit.edu/material/lab{3,4}.zip`）和 2023 版题目，都对应 `VNAV2023` 的目录结构。Lab2 用的也是 `VNAV2023`。因此本方案选用 `VNAV2023`。

### 需要向助教确认（用户负责）

1. **“完成 av-desired 转动”具体检查什么。** `av-desired` 是 `traj_publisher` 广播的期望位姿 TF 帧。官方代码里，期望 yaw 已经按 `-t/2` 随时间转动了。这个给分点可能是检查 rviz 里该帧沿圆运动并旋转，也可能是检查无人机的偏航能跟上它。
2. **分值。** 课程给两道简答题各 25 分，MIT 原题是 10 分和 20 分。以课程为准。

## 2. 环境（阶段 0）

已确认：WSL 里是 Ubuntu 20.04.6 + Noetic，`catkin` 可用，`~/vnav_ws` 已存在（里面有 Lab2 的包），显卡 RTX 4070 SUPER 可见，`DISPLAY=:0` 可用。

| # | 任务 | 负责 |
| --- | --- | --- |
| 0.1 | 获取 `VNAV2023` 代码，把 lab3 的包复制进 `~/vnav_ws/src`，克隆 `mav_comm`；下载 `lab3.zip`（30 MB）和 `lab4.zip`（52 MB），解压到 `~/vnav-builds` | Claude |
| 0.2 | 执行 `sudo apt install ros-noetic-ackermann-msgs`；Lab4 的依赖等编译时一并列出 | 用户 |
| 0.3 | 在 Windows 桌面上打开一个 Ubuntu-20.04 终端（WSLg 窗口才会显示在桌面上），并保持 v2rayN 开启 | 用户 |
| 0.4 | 用 `pip install` 装 tesse-interface，运行 `catkin build`，启动模拟器、bridge 和 rviz 试运行 | Claude |

**完成标准：** 模拟器窗口出现在 Windows 桌面上，rviz 里能看到 `base_link_gt` 和 IMU 箭头，留下启动截图。同时记录模拟器帧率；如果 Unity 只能用软件渲染，要尽早发现。

## 3. Lab3 任务与证据

| # | 给分点 | 做法 | 报告证据 |
| --- | --- | --- | --- |
| 3.1 | 简答题 1（25 分）：tf2 和 msg 互转、取标量、取 yaw、转成 Eigen 矩阵 | 写出答案，并在 WSL 里编译一个小程序实际运行 | 答案、程序输出 |
| 3.2 | 简答题 2（25 分）：(A) F 矩阵的秩；(B) 二次阻力补偿 | 推导两种布局的 F 矩阵并比较秩；把阻力项写进控制律作为前馈 | 推导过程（用 numpy 验证秩） |
| 3.3 | ROS 通信（10 分） | `controller_node.cpp` 的 PART 1–4：订阅、发布、定时器和回调。注意角速度要从世界系转到机体系 | `rqt_graph`、`rostopic hz /rotor_speed_cmds` |
| 3.4 | 代码主体（20 分） | PART 5：计算 eₓ, eᵥ, e_R, e_Ω，得到 f 和 M，再用 F2W 矩阵换算成 4 个转速（rad/s）。先用 `STATIC_POSE=1` 测定点悬停，再跟圆 | 关键代码、悬停截图、跟圆截图 |
| 3.5 | av-desired 转动（10 分） | 在 rviz 里显示 `av-desired` 和 `base_link_gt` | 不同时刻的截图序列 |
| 3.6 | 调参（10 分） | PART 6：调 kx / kv / kr / komega | 增益对比表；用 `rosbag record /current_state /desired_state` 录数据，画位置误差曲线 |
| 3.7 | 飞一圈的视频 | 先在 Linux 里用 ffmpeg 录屏；不行就由用户在 Windows 上按 Win+Alt+R 录 | 视频文件 |

论文和代码之间的坐标约定差异：ROS 的 z 轴朝上，论文朝下；机体 x 轴在两臂之间的 45° 方向；c_τf = c_d / c_f。这些写进报告的“实验过程分解”。

## 4. 进度（Lab3 + Lab4）

| 日期 | 内容 |
| --- | --- |
| 10/13–10/15 | 阶段 0；Lab3 的 3.1–3.4 |
| 10/16–10/18 | Lab3 的 3.5–3.7；Lab4 的简答题和 Part 0 |
| 10/19–10/21 | Lab4 竞速、提速；Lab3 报告初稿 |
| 10/21–10/22 | Lab4 报告；共同完成两份报告的个人思考部分；远程演示彩排 |
| 10/23 | 现场检查 |

## 5. 现场演示准备

- Windows 主机设置为不休眠、不自动更新重启，Tailscale 和 Moonlight（Sunshine）开机自启。
- 写好两份一键启动脚本：Lab3 跟圆、Lab4 竞速。现场只需要运行一条命令。
- 10/22 用手机热点模拟校园网，从外网完整彩排一次：Moonlight 连接、启动、飞行。
- 备选方案：现场网络不通时，展示录屏和 rosbag 回放。

## 6. 风险

1. **模拟器在 WSLg 下的性能未知。** 如果帧率太低，会影响控制效果。阶段 0 优先验证。
2. **依赖网络代理。** pip 安装和 Lab4 依赖编译都要联网下载，v2rayN 关掉就会失败。
3. **WSL 重启后要重开终端。** 每次重启后，都要用户先在 Windows 桌面上打开一个 Ubuntu 终端，模拟器窗口才会出现在桌面上。
