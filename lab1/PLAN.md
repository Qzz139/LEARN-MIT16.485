# Lab 1 实施方案

状态：执行中，2026-09-24。得分点 1–3 已在远程 x86-64 主机的 WSL 2 Ubuntu 20.04.6 中完成；实测记录见 [environment.txt](results/environment.txt)、[compile_examples.txt](results/compile_examples.txt) 和 [shell.txt](results/shell.txt)。C++ 问答、实践及报告待完成。

目标：搭好后续课程可复用的 Linux 开发环境，完成 Lab 1 各项练习，形成可复现的代码、实验报告和现场演示。

## 1. 以什么要求为准

以本课程 [评分说明](../syllabus.md)、[Lab 1 任务入口](README.md) 和 [课件](Lab1.pptx) 为依据；用 [MIT 2023 Lab 1](https://vnav.mit.edu/labs_2023/lab1/) 补充题目和示例。MIT 网页的分值、历史截止日期、MIT 专属账号及仓库提交规则，不直接套用到本课程。

| 评分部分 | 本课程分值 | 计划完成内容 | 验收证据 |
| --- | ---: | --- | --- |
| Ubuntu 安装与配置 | 40 | 可用的 Ubuntu 20.04、软件源与开发工具 | 系统及架构信息、工具版本、配置过程与运行记录 |
| 编译示例代码 | 5 | 编译并运行教学示例，理解编译和链接流程 | 源文件、编译命令、实际输出 |
| Shell 操作 | 5 | 文本统计、输出追加，练习文件和权限操作 | `exercise1.txt`、`fortunes.txt`、命令记录 |
| C++ 问答 | 25 | 按原题逐题解释运算符、引用指针和数值类型 | `cpp-warmup.txt`、必要的小程序验证 |
| C++ 实践 | 25 | 完成 `RandomVector` 的全部方法 | 完整源代码、统计及直方图输出、边界验证 |

表中的验收证据、下文目录及边界验证是实施建议，并非新增评分条款。课件未指定截图数量，也未要求逐一运行全部教程示例。

Git 学习贯穿实验；本课程评分表没有单列 Git 分数。课程还要求单独实验检查，只有报告不能代替检查。过程分解和个人思考分别占检查评价的 30% 和 35%，因此每项均应记录“怎么做、为何这样做、结果说明什么”。

## 2. 环境路线：先定设备，再安装

课程指定 Ubuntu 20.04，课件第 2 页推荐课堂使用虚拟机；后续 Lab 2 对应的 MIT 教程使用 ROS Noetic，所以本方案保留这套版本组合。[MIT 环境要求](https://vnav.mit.edu/labs_2023/lab1/ubuntu.html)、[Lab 2 ROS 安装说明](https://vnav.mit.edu/labs_2023/lab2/ros.html)。

当前工作区宿主机为 macOS / arm64；Lab 1 实际使用远程 Windows x86-64 主机上的 WSL 2 Ubuntu 20.04。下表保留其他路线供后续实验选择：

| 可用设备 | 建议路线 | 开始前需核实 |
| --- | --- | --- |
| 已有 Ubuntu 20.04 机器 | 复用并记录环境；补齐开发工具 | 是否有安装软件权限、是否能保留实验文件 |
| 可用 x86-64 电脑或实验室电脑 | 覆盖全部 Lab 时优先原生 Ubuntu 20.04 amd64（独立安装或双系统）；Lab 1/2 可先用虚拟机 | Ubuntu 安装方式、图形性能与磁盘空间 |
| 仅有当前 Apple 芯片 Mac | 用 UTM 的 ARM64 虚拟机路线评估 Ubuntu 20.04；先验证软件包和桌面 | 后续 Noetic、RViz 及课程依赖能否运行；不能直接承诺后续所有 Lab 均兼容 |
| 打算使用树莓派 | 树莓派 4 可评估 Ubuntu 20.04 ARM64 完成 Lab 1/2 等任务；Lab 3/4 的仿真需另有 x86-64 电脑 | 树莓派型号、内存和系统版本；树莓派 5 的官方 Ubuntu 支持从 24.04 LTS 起 |

Apple 芯片上的 ARM64 虚拟化与 x86-64 模拟是不同路线；UTM 官方说明后者性能更低。若只能使用 Mac，优先评估 ARM64，并尽早做 Lab 2 图形环境验证；若后续依赖受阻，再转实验室 x86 环境。[UTM 官方说明](https://mac.getutm.app/)。

树莓派也不能作为“后续所有 Lab 都可独立完成”的默认保证：MIT 2023 [Lab 3](https://vnav.mit.edu/labs_2023/lab3/exercises.html) 和 [Lab 4](https://vnav.mit.edu/labs_2023/lab4/exercises.html) 分别要求运行预编译的 `lab3.x86_64` 和 `lab4.x86_64` Unity 仿真程序，ARM 设备不能原样执行。树莓派可以承担部分 ROS、C++、视觉代码的开发；仿真演示和 Lab 9 的完整 SLAM 数据集建议预留 x86-64 电脑。[Ubuntu 树莓派支持表](https://ubuntu.com/hardware/docs/boards/how-to/ubuntu_supported/raspberry-pi/)。

若 x86 主机原来运行 Windows，三种方式按全课程适用性排序：双系统原生 Ubuntu 优先；虚拟机可先做早期实验，但应尽早试跑 Lab 3 Unity 仿真和 RViz；WSL2 更适合作为代码与命令行辅助环境。WSL2 支持单个 Linux 图形应用，但并非完整桌面，默认 NAT 网络也可能增加仿真桥接配置。[WSL 图形应用](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps)、[WSL 网络](https://learn.microsoft.com/en-us/windows/wsl/networking)。虚拟机具备 3D 加速支持，但实际帧率需在目标机器验证。[VirtualBox 3D 说明](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/guestadditions.html)。双系统安装前备份数据；若 Windows 启用 BitLocker，先核对密钥与安装流程。[Ubuntu 双系统安装说明](https://ubuntu.com/tutorials/install-ubuntu-desktop)。

虚拟机资源建议从 4 核、4–8 GB 内存、40–60 GB 磁盘起步，按宿主机余量调整；这是实施建议，不是评分条件。x86 安装镜像可从 [Ubuntu 20.04.6 官方目录](https://releases.ubuntu.com/20.04/) 获取；ARM64 需要选择对应架构的镜像，不能混用 amd64 ISO。

Ubuntu 20.04 已于 2025 年 5 月结束标准维护；实施时需检查实际软件源和依赖是否可用，旧教程命令不能视为已经验证成功。为匹配课程继续保留版本，不擅自把课程工程迁移到其他 Ubuntu/ROS 版本。[Ubuntu 生命周期](https://ubuntu.com/about/release-cycle)。

### 环境配置和验收

已在目标 Ubuntu 中以 root 执行以下命令，并记录了实际输出；`wget`、Eigen 和 fortune 数据包按后续练习需要再安装，详见 [environment.txt](results/environment.txt)：

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential cmake git

cat /etc/os-release
uname -m
g++ --version
cmake --version
git --version
```

已验证软件源联网、普通用户终端和工具版本，实测信息保存在 `results/environment.txt`。编辑器、文件共享和 WSL 备份按后续实验需要配置。

退出条件：Ubuntu 能启动；依赖安装完成；`g++`、CMake 和 Git 可用；能在 Ubuntu 内编译并运行最小 C++ 程序。Mac 上的编译结果可辅助开发，最终保留目标 Ubuntu 中的验收结果。

## 3. 具体执行步骤

### A. 编译教学示例，建立工具链概念

课程要求编译示例代码，但本地材料未指定必须运行哪些示例。建议先完成 Hello World，再按学习需要覆盖 `std::vector`、类和 Eigen，并跑通一个 CMake 多文件工程。所选示例保存代码、编译命令和输出，并能解释头文件、源文件、目标文件、可执行文件各自的作用。

直接编译统一使用 C++11 与基础告警。CMake 工程使用独立构建目录，例如在相应示例目录执行：

```bash
cmake -S . -B build
cmake --build build
```

CMake 的作用是组织构建，实际编译仍由编译器完成。此处作为 Lab 2 构建流程的准备。[C++ 教程](https://vnav.mit.edu/labs_2023/lab1/cpp.html)、[CMake 示例](https://vnav.mit.edu/labs_2023/lab1/cmake.html)。

### B. Shell：让结果可以复核

依照 [练习页](https://vnav.mit.edu/labs_2023/lab1/exercises.html) 完成文本统计与五次 fortune 追加，并将所用命令与解释放入记录。

1. 下载题目指定的 `dante.txt`，保留下载地址、日期和文件 SHA-256，确保后续统计使用同一份输入。
2. 用 `wc -l`、`wc -w` 统计换行数和单词数；用 `grep` 统计非空行。在 `exercise1.txt` 中明确是否把“只包含空格/制表符”的行算作空行，必要时列出两种口径。留意文件末尾没有换行时，`wc -l` 与人读到的文本行数可能不同。
3. 先单独运行一次 `fortune` 验证安装，再将后续五次输出用 `>>` 追加至 `fortunes.txt`。准备文件时只初始化一次，记录实际调用次数；一条 fortune 可能多行，不能用文件行数代替调用次数。若命令不在 PATH 中，检查 `/usr/games/fortune`。
4. 补练目录切换、复制移动、权限、管道和重定向，能现场解释 `>` 与 `>>`、`|` 与文件输出的区别。

Git 过程记录：在实验开始、Shell 完成、C++ 完成、报告完成时分别形成清晰提交。分支合并冲突练习放在临时练习仓库中，保存解决过程与提交图。远程提交使用本课程实际要求，不申请 MIT 专属仓库，也不修改当前课程仓库的归属。

### C. C++ 问答：每题给推导

按照原题顺序编写 `cpp-warmup.txt`，覆盖运算符 2 题、引用和指针 4 题、数值类型 4 题。建议每题统一为“题号 → 结论 → 逐步解释 → 必要的运行验证”。

重点理解前置/后置自增、三目运算、引用别名、解引用和指针偏移、引用传参、整数与浮点类型、截断转换、有符号/无符号与布尔条件。涉及类型长度时，区分语言保证与本机 `sizeof` 实测，不把单个平台的字节数写成普遍标准。

### D. RandomVector：先统计，再分桶，再展示

从 [官方 Lab 1 源码](https://github.com/MIT-SPARK/VNAV-labs/tree/master/lab1) 获取模板并记录提交版本，保留原有类接口和演示入口，在 `random_vector.cpp` 中补全 TODO。基础实现不使用 `<algorithm>` 提供的函数；可选版本另行保存，且不将 MIT 的可选加分当成本课程已确认的加分项。

| 方法 | 实现思路 | 重点检查 |
| --- | --- | --- |
| 构造函数 | 填充指定长度的随机浮点向量，映射至 `[0, max_val]` | 使用浮点运算，避免整数除法；沿用入口中的随机种子设置 |
| `print()` | 顺序输出所有元素 | 输出元素数与向量长度一致 |
| `mean()` | 单次遍历求和，再除以长度 | 分母有效，结果使用浮点类型 |
| `min()` / `max()` | 从首元素初始化后逐项比较 | 不用任意常数初始化，不访问空向量 |
| `printHistogram(bins)` | 先统计每个桶的数量，再自上而下打印星号列 | 上界归桶、零宽度和计数守恒 |

官方入口使用固定种子 `314159`、20 个元素和 5 个桶。先让这一默认场景通过，再检查边界。相同种子用于同一实现中的复现；不同平台的随机数库可能不同，不要求 Ubuntu 数值逐项等于网页或 Mac 的示例。[官方 main.cpp](https://raw.githubusercontent.com/MIT-SPARK/VNAV-labs/master/lab1/main.cpp)。

直方图采用等宽分桶：`width = (max - min) / bins`。通常区间左闭右开，最后一个桶包含最大值；最大值对应的索引要落在 `bins - 1`，不能访问第 `bins` 个桶。若 `min == max`，走单独分支，本方案约定全部放入第一个桶并在报告中说明。

边界行为属于实现设计：建议对 `size <= 0`、负或非有限的 `max_val`、`bins <= 0` 报清晰错误；允许 `max_val == 0` 并按等值向量处理。原题未逐项规定这些行为，报告应注明自己的选择。

编译与运行验收，在 `RandomVector` 目录执行：

```bash
g++ -std=c++11 -Wall -pedantic -o random_vector main.cpp random_vector.cpp
./random_vector
```

最小验证集合：

- 默认 20 元素、5 桶：长度正确，所有值在约定范围内，且 `min <= mean <= max`。
- 分桶计数：每个桶计数非负，所有桶数量之和等于向量长度；统计验证使用真实数值，不能依赖四舍五入后的显示值。
- 单元素、`max_val == 0`、`bins == 1`、桶数大于元素数：不除零、不越界，图形与计数一致。
- 最大值所在桶：落入最后一个桶；等值向量遵循单独约定。
- 非法参数：符合文档化的错误处理行为。

先完成基础循环版本，再考虑简短的 CMake 构建或标准库对照实验；可选扩展不占用必做项的完成时间。

## 4. 时间安排与里程碑

建议分 4 个工作段完成，合计约 9–14 小时；这是规划估算，下载和环境兼容问题可能增加时间。有现成环境时可压缩第一段。

| 工作段 | 预计用时 | 内容 | 完成标志 |
| --- | --- | --- | --- |
| 第 1 段 | 2–4 小时 | 确定设备，配置 Ubuntu，跑通首个示例 | 环境记录完整，Hello World 可在 Ubuntu 运行 |
| 第 2 段 | 2–3 小时 | 其余示例、Shell、Git 与 C++ 问答 | Shell 产物齐全，10 道题能解释 |
| 第 3 段 | 3–4 小时 | 实现 RandomVector，验证统计和边界 | 默认入口通过，计数守恒，边界结果明确 |
| 第 4 段 | 2–3 小时 | 整理报告、从源代码重跑、演示演练 | 文件完整，重跑成功，能现场回答问题 |

课程说明对 Lab 1 完成周期写有“一周”，其他段落又有“两周”的通用表述；教学日历中 Lab 1/2 检查同时出现在 10 月 9 日和 10 月 23 日。当前资料不能确定唯一截止日，应按助教最新通知确认；内部安排采用一周内完成，不能把较晚日期当作默认延期。

## 5. 交付物组织

建议在现有 `lab1/` 下逐步增加以下内容，保留原始课件和报告模板。环境、示例编译和 Shell 练习产物已完成，C++ 问答、实践和报告仍待完成。

```text
lab1/
  PLAN.md
  exercise1.txt             # Shell 统计结果、命令和口径
  fortunes.txt              # 五次追加的实际输出
  cpp-warmup.txt            # 按题号编排的问答
  examples/                # 教学示例与 CMake 工程
  RandomVector/
    main.cpp
    random_vector.h
    random_vector.cpp
  data/
    dante.txt
  results/
    environment.txt
    compile_examples.txt   # 两种编译方式的命令和输出
    shell.txt              # Shell 命令、数据来源和结果
    random_vector.txt
    validation.md          # 预期行为、实测行为与解释
    screenshots/
  report/
    lab1-report.tex        # 或采用其他报告源文件格式
    lab1-report.pdf
```

构建目录和可执行文件作为本地产物管理；保留重建它们所需的源代码和命令。若提交平台要求不同目录结构，在提交时调整打包布局。

报告采用“目的与任务 → 环境配置 → 各部分方法和结果 → 问题分析 → 个人总结”的结构，代码与文字记录或终端截图配解释。现有 [template.tex](Materials1LabReport/template.tex) 可参考，但其中学生信息、`Lab 3 Report`、组号和旧日期都是占位内容，需要替换；同目录下的 `Torsion.csv` 不是当前 Lab 1 的明确任务输入。

## 6. 提交与现场检查清单

- [x] Ubuntu、工具版本和实际设备架构有记录；见 [environment.txt](results/environment.txt)。
- [x] 所选教学示例能运行，并能说明实际编译命令；见 [compile_examples.txt](results/compile_examples.txt)。
- [x] Shell 统计可从保存的输入重新计算，fortune 确为五次追加；见 [shell.txt](results/shell.txt)。
- [ ] C++ 问答覆盖原题，答案有推导并体现平台差异。
- [ ] RandomVector 全部 TODO 完成，基础实现未使用 `<algorithm>` 函数。
- [ ] 保留默认入口演示和边界验证结果，直方图计数守恒。
- [ ] 报告使用真实实验截图和结果，去除模板中的旧个人信息。
- [ ] 从干净构建目录重跑通过，命令中的路径与实际文件一致。
- [ ] 能现场解释自增、指针与引用、输出追加、随机种子和分桶上界处理。
- [ ] 按助教通知完成报告/代码提交及单独实验检查。

资料范围说明：本方案已核对本地课程说明、7 页 Lab 1 课件、报告模板及 MIT 链接；仓库中的 Notion 简要说明链接本次未能访问，若其中有本校额外要求，应补充到本方案。
