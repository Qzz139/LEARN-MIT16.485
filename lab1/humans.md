# Lab 1 手操复现说明书

本说明书按本课程的五个得分点，从零操作到运行验收。目标环境是 **Windows x86-64 主机上的 WSL 2 / Ubuntu 20.04.6**；Mac 只用来连接或阅读文件。所有 Linux 命令都在 Ubuntu 的 Bash 中运行，除非标明为「Windows PowerShell」。命令块中的 `$`、`PS>` 等提示符均未写入，复制代码块即可执行。英文正式报告是 [lab1-report.pdf](report/lab1-report.pdf)；这里是给操作者看的中文说明，不替代报告。

复现分数对应：Ubuntu 安装配置 40、编译示例 5、Shell 5、C++ 问答 25、C++ 实践 25。每节都说明应看到什么、保存什么。文中的旧输出是 2026-09-24 在 `qz` 用户的 Ubuntu 20.04.6 上得到的参照值；你的日期、`fortune` 内容和其他 C 库上的随机数可以不同。**不要把重跑结果冒充原实验截图**。已有五张报告图是由当时 SSH/WSL 的文字输出排版得到，明确不是原生窗口截图。

## 0. 进入正确的终端，准备独立工作目录

如果 `Ubuntu-20.04` 已经存在，直接在 Windows PowerShell 中运行：

```powershell
wsl.exe --list --verbose
wsl.exe --distribution Ubuntu-20.04
```

第一条列出发行版，确认 `Ubuntu-20.04` 的 `VERSION` 为 `2`；第二条进入它。此前这台主机还装有另一个名为 `Ubuntu` 的发行版，**不要只输入 `wsl`**，否则可能进入错误版本。若新安装的发行版显示为不同名称，后续 `--distribution` 要改用列表中的实际名称。若用 Mac 远程操作，可在 Mac 终端运行 `ssh -tt qz@100.84.51.48 wsl.exe --distribution Ubuntu-20.04`；IP 或 SSH 凭据变化时以 Windows 主机的当前地址为准。需要输入密码时在终端本地输入，不要写进文件。

如果是**新 Windows 主机，且尚无 Ubuntu 20.04**，在管理员 PowerShell 执行下面的安装段；已有发行版就跳过整个安装段。WSL 首次启用可能要求重启。`.wsl` 文件安装需要较新的 WSL（微软文档写明 2.4.4 或以上）；运行 `wsl.exe --version` 核对。Ubuntu 镜像及散列来自 [Ubuntu 官方目录](https://releases.ubuntu.com/focal/)与 [SHA256SUMS](https://releases.ubuntu.com/focal/SHA256SUMS)，从文件安装的语法见 [微软 WSL 文档](https://learn.microsoft.com/en-us/windows/wsl/build-custom-distro)。

```powershell
wsl.exe --version
wsl.exe --update
$Image = Join-Path $env:USERPROFILE 'Downloads\ubuntu-20.04.6-wsl-amd64.wsl'
curl.exe -L --fail --silent --show-error --output $Image https://releases.ubuntu.com/focal/ubuntu-20.04.6-wsl-amd64.wsl
(Get-FileHash $Image -Algorithm SHA256).Hash.ToLower()
wsl.exe --install --from-file $Image
wsl.exe --list --verbose
wsl.exe --distribution Ubuntu-20.04
```

第 1 行显示 WSL 版本；第 2 行更新 WSL 本体；第 3 行确定下载位置；第 4 行下载 amd64 镜像；第 5 行的结果必须是 `a9073f3726aab9661076506603706eadf284b80a791dec3adfde8e1989906fa4`，**不一致就停止，不安装**；第 6 行注册发行版；最后两行检查并进入。若系统提示 WSL 功能尚未启用，先按 [微软安装说明](https://learn.microsoft.com/en-us/windows/wsl/install)执行管理员 `wsl --install` 并按要求重启，然后再执行上述镜像安装段。首次启动按提示建立 Linux 用户 `qz` 和密码；已有用户不重复创建。

以下直到末尾均在 **Ubuntu Bash** 执行。先确认身份与版本，再安装依赖：

```bash
whoami
cat /etc/os-release
uname -m
sudo -v
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y build-essential cmake git curl fortune-mod fortunes-min
g++ --version
cmake --version
git --version
make --version
```

`whoami` 应为 `qz`；`/etc/os-release` 中应有 `VERSION_ID="20.04"`，架构应为 `x86_64`。`sudo -v` 只验证你能输入自己的 Linux 密码；`apt-get update` 更新软件包索引；`upgrade -y` 安装可用更新；`install -y` 安装编译器、CMake、Git、下载工具和 fortune。原实验观测为 g++ 9.4.0、CMake 3.16.3、Git 2.25.1、Make 4.2.1；补丁版本允许随软件源更新。切勿在 Mac 终端运行这些 Ubuntu 安装命令。

取得课程仓库并复制一份**独立工作目录**，后续重建、清空 `fortunes.txt` 只影响这份副本：

```bash
cd "$HOME"
git clone https://github.com/Qzz139/26second-seme.git
git -C "$HOME/26second-seme" log -1 --oneline
mkdir -p "$HOME/lab1-replay"
cp -a "$HOME/26second-seme/lab1/." "$HOME/lab1-replay/"
cd "$HOME/lab1-replay"
pwd
```

`git clone` 取回源码和已保存的数据；如仓库要求登录，用你自己的 GitHub 凭据完成。若 `$HOME/26second-seme` 已存在，就跳过 `git clone`；若无法访问 GitHub、但原实验目录 `/home/qz/lab1` 还在，可改用 `cp -a /home/qz/lab1/. "$HOME/lab1-replay/"` 复制该目录。`git log` 告诉你拿到的版本；原实验的提交是 `1566792`，若最新版本已有后续改动，可在复制前对仓库执行 `git -C "$HOME/26second-seme" checkout 1566792` 以固定源码。`mkdir` 建工作目录，`cp -a .../.` 把 `lab1` 内容复制进去，`cd` 切到副本，`pwd` 应显示 `/home/qz/lab1-replay`（若用户名不同，前缀随之变化）。下文所有相对路径都从这里算起。**保持同一个 Bash 会话，或重新进入时先 `cd "$HOME/lab1-replay"`。**

## 1. Ubuntu 安装与配置（40 分）

记录真实环境，不只凭安装成功的提示判断。下面每条都可以单独执行；`tee` 会把终端输出同时写进复现记录。已有原实验记录在 [results/environment.txt](results/environment.txt)，重跑文件放进 `results/replay/`。

```bash
mkdir -p results/replay
cat /etc/os-release | tee results/replay/os-release.txt
uname -m | tee results/replay/architecture.txt
id | tee results/replay/user.txt
dpkg-query -W build-essential cmake git | tee results/replay/packages.txt
g++ --version | head -n 1 | tee results/replay/gcc-version.txt
cmake --version | head -n 1 | tee results/replay/cmake-version.txt
git --version | tee results/replay/git-version.txt
```

`mkdir -p` 建证据目录；`cat` 显示系统版本；`uname -m` 显示 CPU 架构；`id` 显示普通用户及 `sudo` 组；`dpkg-query -W` 显示实际安装包版本；最后三行显示工具版本。管道 `|` 把左边命令输出交给右边，`tee` 同时打印和写文件。要演示编译器真能用，而不只是安装包存在，亲手写入最小程序：

**`results/toolchain_smoke.cpp`：**

```bash
cat > results/toolchain_smoke.cpp <<'LAB1_CODE'
#include <iostream>

int main() {
  std::cout << "Ubuntu 20.04 toolchain OK\n";
  return 0;
}
LAB1_CODE
```

```bash
g++ -std=c++11 -Wall -Wextra -pedantic results/toolchain_smoke.cpp -o results/replay/toolchain_smoke
./results/replay/toolchain_smoke | tee results/replay/toolchain_smoke.txt
```

源码第 1 行导入 `std::cout`，第 3–6 行是 `main`：打印一句话并返回 0。`g++` 编译没有报错且运行输出 `Ubuntu 20.04 toolchain OK` 才算通过。`-std=c++11` 指定语言版本，`-Wall -Wextra -pedantic` 开启诊断，`-o` 指定可执行文件位置。若要原生窗口截图，显示此终端后在 Windows 按 `Win+Shift+S`，框选窗口并在截图工具中保存；不要把排版图称为窗口截图。

## 2. 编译示例代码（5 分）

先手写单文件 Hello World，再编译与运行：

**`examples/hello.cpp`：**

```bash
cat > examples/hello.cpp <<'LAB1_CODE'
#include <iostream>

int main() {
  std::cout << "Hello from Lab 1 on Ubuntu 20.04!\n";
  return 0;
}
LAB1_CODE
```

```bash
g++ -std=c++11 -Wall -Wextra -pedantic examples/hello.cpp -o results/replay/hello
./results/replay/hello | tee results/replay/hello.txt
```

六行源码依次是导入输出库、空行、`main` 开始、写一行输出、返回成功状态、函数结束。应输出 `Hello from Lab 1 on Ubuntu 20.04!`。编译命令中的源文件是 `examples/hello.cpp`，`-o` 后是生成的程序；后一行 `./` 表示运行当前目录下相对路径指向的可执行文件。

然后手写四个 CMake 工程文件。它们演示「声明 → 定义 → 编译静态库 → 链接入口程序」的完整关系：

**`examples/cmake-example/message.hpp`：**

```bash
cat > examples/cmake-example/message.hpp <<'LAB1_CODE'
#pragma once

#include <string>

std::string lab1_message();
LAB1_CODE
```

**`examples/cmake-example/message.cpp`：**

```bash
cat > examples/cmake-example/message.cpp <<'LAB1_CODE'
#include "message.hpp"

std::string lab1_message() {
  return "CMake library link OK";
}
LAB1_CODE
```

**`examples/cmake-example/main.cpp`：**

```bash
cat > examples/cmake-example/main.cpp <<'LAB1_CODE'
#include <iostream>

#include "message.hpp"

int main() {
  std::cout << lab1_message() << '\n';
  return 0;
}
LAB1_CODE
```

**`examples/cmake-example/CMakeLists.txt`：**

```bash
cat > examples/cmake-example/CMakeLists.txt <<'LAB1_CODE'
cmake_minimum_required(VERSION 3.10)
project(lab1_cmake_example LANGUAGES CXX)

add_library(message message.cpp)
target_compile_features(message PUBLIC cxx_std_11)

add_executable(example main.cpp)
target_link_libraries(example PRIVATE message)
LAB1_CODE
```

`message.hpp` 第 1 行防止头文件重复包含，第 3 行引入字符串类型，第 5 行**只声明** `lab1_message()`；`message.cpp` 引入声明并在函数体返回固定字符串；`main.cpp` 引入输出库和头文件，再调用函数并打印结果。`CMakeLists.txt` 前两行规定最低 CMake 版本和 C++ 项目，第 4–5 行把 `message.cpp` 建成要求 C++11 的库，第 7–8 行建立可执行文件并把库链接进去。逐条执行：

```bash
cmake -S examples/cmake-example -B results/replay/cmake-build
cmake --build results/replay/cmake-build
./results/replay/cmake-build/example | tee results/replay/cmake-example.txt
```

`-S` 指源码目录，`-B` 指新构建目录；第二行实际调用编译工具，最后一行运行。应输出 `CMake library link OK`。若编译报 `undefined reference to lab1_message`，先检查 `target_link_libraries(example PRIVATE message)` 是否逐字存在。原实验命令和 Ubuntu 输出在 [compile_examples.txt](results/compile_examples.txt)。

## 3. Shell 操作（5 分）

### 3.1 Dante 文本统计

课程题目指定的 `dante.txt` 已保存在 `data/`。**以仓库内这份文件做精确复现**，因为原始 GitHub `master` 路径会随上游提交变化。先核对字节数与 SHA-256，再统计：

```bash
wc -c data/dante.txt
sha256sum data/dante.txt
LC_ALL=C wc -l -w data/dante.txt
LC_ALL=C grep -cve '^[[:space:]]*$' data/dante.txt
LC_ALL=C grep -cve '^$' data/dante.txt
```

这五行依次给出文件字节数、内容散列、换行数与单词数、非空白行数、非零长度行数。应依次核对 `557042` 字节、SHA-256 `1cd578e12a35c885028c64ee6c6b3ee1643be9dd8e45e0a9fbfa77acb2f6c279`、`19567` 行、`97676` 词、`14338` 非空白行。最后两个 `grep` 在这份文件中都得 `14338`，说明不存在只含空格或制表符的非空行。`wc -l` 计算的是换行符；这个文件以换行结尾。`LC_ALL=C` 固定词边界口径，避免 macOS 默认区域设置出现不同词数。

若想练习**亲自下载**，先备份仓库内的原件，再另存下载文件；网络故障时不要改用未经核对的文本。下列第一条取原题的 GitHub Raw 路径；本次实验曾遇到连接被重置，失败时可用第二条 CDN 路径。随后比较散列，必须与上述固定值一致才能用它替换原件：

```bash
curl -fL https://raw.githubusercontent.com/dlang/dmd/master/druntime/benchmark/extra-files/dante.txt -o results/replay/dante-download.txt
sha256sum results/replay/dante-download.txt
```

仅当下载失败时改用：

```bash
curl -fL https://cdn.jsdelivr.net/gh/dlang/dmd@master/druntime/benchmark/extra-files/dante.txt -o results/replay/dante-download.txt
sha256sum results/replay/dante-download.txt
```

把题目答案写成文字记录。第 3 题的「空行」按空字符串或全空白字符处理；原实验答案在 [exercise1.txt](exercise1.txt)。

```bash
cat > results/replay/exercise1.txt <<'ANSWERS'
1. Lines: 19567; command: LC_ALL=C wc -l data/dante.txt
2. Words: 97676; command: LC_ALL=C wc -w data/dante.txt
3. Nonblank lines: 14338; command: LC_ALL=C grep -cve '^[[:space:]]*$' data/dante.txt
Input SHA-256: 1cd578e12a35c885028c64ee6c6b3ee1643be9dd8e45e0a9fbfa77acb2f6c279
ANSWERS
cat results/replay/exercise1.txt
```

`cat > ... <<'ANSWERS'` 表示把后面每行原样写到文件，直到单独一行 `ANSWERS` 结束；`>` 是创建或覆盖，最后的 `cat` 用来复核。

### 3.2 fortune：先试一次，再追加五次

下列命令在**副本**目录执行。先单独运行一次，不计入文件；随后只清空一次文件，用五条 `>>` 命令追加五次。`fortune` 的内容随机，每次字节数、行数与旧记录不同是正常现象。

```bash
/usr/games/fortune
: > fortunes.txt
/usr/games/fortune >> fortunes.txt
/usr/games/fortune >> fortunes.txt
/usr/games/fortune >> fortunes.txt
/usr/games/fortune >> fortunes.txt
/usr/games/fortune >> fortunes.txt
wc -c fortunes.txt
cat fortunes.txt
```

第 1 行是安装后的独立试运行；第 2 行初始化空文件（冒号 `:` 是不输出内容的 Bash 内建命令）；第 3–7 行**各调用一次**并把输出追加到末尾；`wc -c` 显示总字节数；`cat` 检查确实保存了内容。不要在五次调用之间执行 `>`，那会覆盖前面的结果。原实验的文件 [fortunes.txt](fortunes.txt) 是 441 字节、9 个文本行，但这是随机结果，**9 行不代表调用了 9 次**。如果要保留可审计的五次累计大小，改用仓库的 [append_fortunes.sh](results/append_fortunes.sh)；该脚本把路径写死为 `/home/qz/lab1/fortunes.txt`，直接运行会碰原目录，因此本说明书故意使用上述手工命令。

### 3.3 目录、复制移动、权限、管道

```bash
mkdir -p shell-demo
cd shell-demo
pwd
printf 'shell practice\n' > original.txt
cp original.txt copy.txt
mv copy.txt renamed.txt
chmod 640 renamed.txt
find . -maxdepth 1 -type f -printf '%f\n' | sort
stat -c '%a' renamed.txt
cat renamed.txt | wc -w
cd ..
```

从上到下依次是建目录、进入目录、显示当前位置、创建一行文件、复制、重命名、设置拥有者读写/同组只读/其他人无权限、列出文件并排序、核对权限数值 `640`、通过管道数出 `2` 个单词、返回 Lab 1 目录。这里的 `>` 会覆盖 `original.txt`；`|` 把标准输出送到下一命令而不写文件。原 Ubuntu 命令记录在 [shell.txt](results/shell.txt)。

## 4. C++ 问答（25 分）

题目一共十问，按 O1–O2（运算符）、R1–R4（引用和指针）、N1–N4（数值类型）整理。先读 [cpp-warmup.txt](cpp-warmup.txt) 的完整书面答案，再亲手输入下面的验证程序；它把课堂题干中的关键语句放在一起运行。

**`results/cpp_warmup_check.cpp`：**

```bash
cat > results/cpp_warmup_check.cpp <<'LAB1_CODE'
#include <iostream>

void reset(int& value) { value = 0; }

int main() {
  int i = 0, j;
  j = ++i;
  j = i++;
  std::cout << "O1 i=" << i << " j=" << j << '\n';

  i = 42;
  std::cout << "O2 " << ((i < 42) ? "a" : "b") << '\n';

  int original;
  int& alias = original;
  original = 5;
  alias = 10;
  std::cout << "R1 " << original << ' ' << alias << '\n';

  int pointed = 42;
  int* pointer = &pointed;
  *pointer = *pointer**pointer;
  std::cout << "R2 " << *pointer << '\n';

  int values[4] = {42, 24, 42, 24};
  *(values + 2) = *(values + 1) - values[3];
  std::cout << "R3 " << *(values + 2) << '\n';

  j = 42;
  reset(j);
  std::cout << "R4 " << j << '\n';

  std::cout << "N1 sizeof(short,int,long,long long)="
            << sizeof(short) << ',' << sizeof(int) << ','
            << sizeof(long) << ',' << sizeof(long long) << '\n';
  std::cout << "N2 sizeof(float,double)=" << sizeof(float) << ','
            << sizeof(double) << " i=" << static_cast<int>(3.14) << '\n';
  unsigned char c = -1;
  std::cout << "N3 c=" << static_cast<unsigned int>(c) << '\n';
  i = 42;
  if (i) i = 0;
  else i = 43;
  std::cout << "N4 i=" << i << '\n';
}
LAB1_CODE
```

```bash
g++ -std=c++11 -Wall -Wextra -pedantic results/cpp_warmup_check.cpp -o results/replay/cpp_warmup_check
./results/replay/cpp_warmup_check | tee results/replay/cpp_warmup_check.txt
```

源码逐段读：`reset(int& value)` 的 `&` 让参数成为调用者变量的别名；O1 的 `++i` 先加再取值而 `i++` 先取旧值再加；O2 中 `42 < 42` 为假；R1 的 `alias` 与 `original` 是同一对象；R2 的 `*pointer**pointer` 解析为 `(*pointer) * (*pointer)`；R3 的 `values + 2` 指向第三个元素；R4 的 `reset(j)` 把调用者的 `j` 改成 0；N1/N2 用 `sizeof` 实测类型大小；N3 把 `-1` 转成 8 位 `unsigned char`；N4 把非零整数 42 当作条件真值。`std::cout` 的每一行都标了题号，便于把输出与答案对应。

| 题号 | 应得结果 | 现场解释重点 |
| --- | --- | --- |
| O1 | `i=2 j=1` | 前置/后置自增各自何时取值。 |
| O2 | `b` | 条件 `42 < 42` 为假，三目运算符选第三项。 |
| R1 | `10 10` | 引用是别名；改引用即改原变量。 |
| R2 | `1764` | 指针解引用后做 `42*42`，不是乘方。 |
| R3 | `0` | 第三元素变为第二减第四，即 `24-24`。 |
| R4 | `0` | 引用参数修改调用者的值。 |
| N1 | `2,4,8,8` | 这是本次 Ubuntu x86-64 的 `sizeof`，不是所有平台的规定字节数。 |
| N2 | `float=4,double=8,i=3` | `3.14` 赋给 `int` 截掉小数，不四舍五入。 |
| N3 | `255` | 题目规定 `char` 为 8 位，`-1` 转无符号按模 256。 |
| N4 | `0` | 非零条件为真，执行 `if` 分支。 |

若大小或随机数在另一平台不同，先核对架构和编译器，不要修改语言规则结论来迁就某份输出。原 Ubuntu 运行记录在 [cpp_warmup_check.txt](results/cpp_warmup_check.txt)。

## 5. C++ 实践：RandomVector（25 分）

下面四个代码块是**完整可复制**的课程实现与验证代码，没有省略函数体。虽然独立工作目录已经从仓库复制了这些文件，仍可按顺序手敲/粘贴覆盖副本，以理解每一行。写入顺序为头文件、默认入口、实现、测试。

**`RandomVector/random_vector.h`：**

```bash
cat > RandomVector/random_vector.h <<'LAB1_CODE'
#include <iostream>
#include <vector>

class RandomVector{
  std::vector<double> vect;

  public:
    RandomVector(int size, double max_val = 1);
    void print();
    double mean();
    double max();
    double min();
    void printHistogram(int bins);
};
LAB1_CODE
```

头文件逐行含义：`<iostream>` 支持输出，`<vector>` 提供动态数组；`class RandomVector` 开始类定义；`vect` 是私有的浮点容器；`public:` 以下六行是构造、打印、平均值、最大值、最小值和直方图的方法声明。`max_val = 1` 使第二个构造参数可省略。末尾的分号结束类定义。这里保留了课程模板的接口。

**`RandomVector/main.cpp`：**

```bash
cat > RandomVector/main.cpp <<'LAB1_CODE'
#include <cstdlib> // required for srand
#include <iostream>
#include "random_vector.h"

int main(){
  // initialize rand with constant seed for reproducibility
  std::srand(314159);

  RandomVector rv(20);
  rv.print();
  std::cout << "Mean: " << rv.mean() << std::endl;
  std::cout << "Min: " << rv.min() << std::endl;
  std::cout << "Max: " << rv.max() << std::endl;

  std::cout << "Histogram:" << std::endl;
  rv.printHistogram(5);
  std::cout << std::endl;
}
LAB1_CODE
```

入口第 1–3 行引入随机函数、输出与类声明；`main` 从第 5 行开始；第 7 行固定种子 `314159`；第 9 行创建 20 个值的对象；第 10–13 行逐项打印向量和统计量；第 15–16 行打印 5 桶直方图；第 17 行输出结尾换行。固定种子只保证**同一种 C 库实现内**可重复，不能保证 Windows、macOS 与 Ubuntu 的序列完全相同。

**`RandomVector/random_vector.cpp`：**

```bash
cat > RandomVector/random_vector.cpp <<'LAB1_CODE'
#include "random_vector.h"

#include <cstdlib>

// Fill the vector with `size` random numbers in [0, max_val].
RandomVector::RandomVector(int size, double max_val) {
  for (int i = 0; i < size; ++i) {
    // Cast to double first: rand() / RAND_MAX would be integer division (almost always 0).
    double unit = static_cast<double>(std::rand()) / RAND_MAX;  // in [0, 1]
    vect.push_back(unit * max_val);
  }
}

void RandomVector::print() {
  for (std::size_t i = 0; i < vect.size(); ++i) {
    if (i > 0) std::cout << ' ';
    std::cout << vect[i];
  }
  std::cout << '\n';
}

double RandomVector::mean() {
  double sum = 0.0;
  for (double value : vect) sum += value;
  return sum / vect.size();
}

// max() and min() start from the first element, not from an arbitrary constant like 0.
double RandomVector::max() {
  double result = vect[0];
  for (double value : vect) {
    if (value > result) result = value;
  }
  return result;
}

double RandomVector::min() {
  double result = vect[0];
  for (double value : vect) {
    if (value < result) result = value;
  }
  return result;
}

void RandomVector::printHistogram(int bins) {
  // Step 1: count how many values fall in each of `bins` equal-width bins over [min, max].
  std::vector<int> counts(bins, 0);
  double low = min(), high = max();
  for (double value : vect) {
    int index = 0;  // if every value is equal (high == low), all go to the first bin
    if (high > low) index = static_cast<int>((value - low) / (high - low) * bins);
    // Bins are [left, right); the maximum itself gives index == bins, so move it
    // into the last bin instead of writing past the end of `counts`.
    if (index == bins) index = bins - 1;
    ++counts[index];
  }

  // Step 2: print the columns from the top row down. A bin gets "***" in every
  // row whose level is at most its count.
  int tallest = 0;
  for (int count : counts) {
    if (count > tallest) tallest = count;
  }
  for (int level = tallest; level > 0; --level) {
    for (int bin = 0; bin < bins; ++bin) {
      if (bin > 0) std::cout << ' ';
      std::cout << (counts[bin] >= level ? "***" : "   ");
    }
    std::cout << '\n';
  }
}
LAB1_CODE
```

实现文件逐行检查要点：

| 源码行 | 作用与不能省的理由 |
| --- | --- |
| 1–3 | 引入类声明和 `rand`。 |
| 5–12 | 构造函数：每次把 `rand()` 转成 `double` 后除以 `RAND_MAX`，得到 [0, 1] 内的数，再乘上界；先转浮点可避免整数除法。 |
| 14–20 | 顺序打印全部元素；仅在非首元素前打印空格，最后补换行。 |
| 22–26 | 累加全部值，除以元素个数得到均值。 |
| 28–43 | 最大/最小值都从首元素初始化，再与其余元素比较，不凭空假设初值（例如 0）。 |
| 45–56 | 第一步：统计每桶个数。索引 `floor((value-low)/(high-low)*bins)`；所有值相等时全部放第一桶，避免除以零；最大值本会算到 `bins`，所以放回末桶 `bins-1`，否则会写出数组边界。 |
| 58–63 | 第二步：找最高桶的高度，确定要打印几行。 |
| 64–70 | 从最高层往下打印，每桶个数不小于当前层时打印 `***`，否则打印三个空格；相邻桶之间插入一个空格。 |

这种分桶约定是左闭右开，最后一桶包含最大值；所有桶的计数之和必须等于元素数。基础实现只用循环和比较，没有调用 `<algorithm>` 的函数。和实验模板一样，程序默认长度和桶数为正数，不做输入检查；等值向量放第一桶是本项目写明的约定。

先编译默认入口并运行；`tee` 把本次输出另存到 `results/replay/`：

```bash
g++ -std=c++11 -Wall -Wextra -pedantic RandomVector/main.cpp RandomVector/random_vector.cpp -o results/replay/random_vector
./results/replay/random_vector | tee results/replay/random_vector.txt
```

本次 Ubuntu 的旧输出应有 `Mean: 0.55804`、`Min: 0.0278694`、`Max: 0.982655`，五桶计数为 `5 1 4 3 7`，合计 20。**判断是否通过时以实际值的范围、`min <= mean <= max`、计数守恒和没有崩溃为准**；补丁或 C 库变化时不要硬凑旧小数。旧完整输出见 [random_vector.txt](results/random_vector.txt)。

最后写一个小测试，检查统计量的大小关系、直方图不丢值、等值向量不除以零；测试程序必须与默认入口分开编译，否则会出现两个 `main`：

**`RandomVector/test_random_vector.cpp`：**

```bash
cat > RandomVector/test_random_vector.cpp <<'LAB1_CODE'
// A few checks for RandomVector. Any failed assert stops the program,
// so the final "passed" line is printed only if every check held.
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>

#include "random_vector.h"

// printHistogram() only prints, so temporarily redirect std::cout into a string.
std::string histogram(RandomVector& rv, int bins) {
  std::ostringstream out;
  std::streambuf* old = std::cout.rdbuf(out.rdbuf());
  rv.printHistogram(bins);
  std::cout.rdbuf(old);
  return out.str();
}

// Every "***" stands for one value in one bin.
int countStars(const std::string& text) {
  int n = 0;
  std::size_t pos = text.find("***");
  while (pos != std::string::npos) {
    ++n;
    pos = text.find("***", pos + 3);
  }
  return n;
}

int main() {
  std::srand(314159);  // same seed as main.cpp
  RandomVector rv(20);
  assert(0.0 <= rv.min() && rv.min() <= rv.mean() && rv.mean() <= rv.max() && rv.max() <= 1.0);

  // No value may be lost or counted twice, including the maximum.
  assert(countStars(histogram(rv, 5)) == 20);
  assert(countStars(histogram(rv, 1)) == 20);
  assert(countStars(histogram(rv, 30)) == 20);  // more bins than values

  // All values equal (max == min): no division by zero, everything in the first bin.
  RandomVector zero(3, 0.0);
  assert(zero.min() == 0.0 && zero.mean() == 0.0 && zero.max() == 0.0);
  assert(histogram(zero, 2) == "***    \n***    \n***    \n");

  std::cout << "All RandomVector checks passed: range, mean, 20 stars for 1/5/30 bins, equal values\n";
}
LAB1_CODE
```

测试源码第 11–18 行的 `histogram()` 暂时把 `std::cout` 导入字符串流，拿到直方图的文字；第 20–29 行数出其中 `***` 的个数，每个 `***` 代表一个值；第 34 行检查 `0 <= min <= mean <= max <= 1`；第 36–39 行要求 5 桶、1 桶、30 桶（多于元素数）时都正好有 20 个 `***`，即没有值丢失，最大值也被计入；第 41–44 行检查三个相等的值全部落在第一桶。`assert` 失败会终止程序，最后一行只有在全部检查通过时才会打印。`std::cout.rdbuf(old)` 必须恢复原输出缓冲，否则后续结果看不到。运行命令：

```bash
g++ -std=c++11 -Wall -Wextra -pedantic RandomVector/test_random_vector.cpp RandomVector/random_vector.cpp -o results/replay/test_random_vector
./results/replay/test_random_vector | tee results/replay/random_vector_validation.txt
```

应看到一行 `All RandomVector checks passed: ...`，见 [random_vector_validation.txt](results/random_vector_validation.txt)。

## 6. 核对证据、现场展示与结束

在副本目录逐条核对文件是否存在，再读旧记录与本次记录：

```bash
test -s results/replay/toolchain_smoke.txt && echo 'Ubuntu/toolchain evidence OK'
test -s results/replay/hello.txt && test -s results/replay/cmake-example.txt && echo 'Compile evidence OK'
test -s results/replay/exercise1.txt && test -s fortunes.txt && echo 'Shell evidence OK'
test -s results/replay/cpp_warmup_check.txt && echo 'C++ answers evidence OK'
test -s results/replay/random_vector.txt && test -s results/replay/random_vector_validation.txt && echo 'RandomVector evidence OK'
grep -n 'passed' results/replay/random_vector_validation.txt
```

`test -s` 要求文件存在且非空；`&&` 只在左侧命令成功时运行右侧；`grep -n` 带行号显示 passed 行。五条 `... evidence OK` 与一条 passed 都出现，才算这次复现的文字证据齐全。旧实验的证据入口是 [environment.txt](results/environment.txt)、[compile_examples.txt](results/compile_examples.txt)、[shell.txt](results/shell.txt)、[cpp-warmup.txt](cpp-warmup.txt)、[validation.md](results/validation.md) 以及正式 PDF。现场需要展示原生截图时，对当前终端窗口截图并保留时间与命令；说明书中的旧图不能代替新的窗口截图。

检查前能口头解释：为何明确选择 `Ubuntu-20.04`；`g++` 与 CMake 各做什么；`>` 与 `>>` 的差别；`wc -l` 与非空行如何计算；前置/后置自增、引用与指针的作用；随机种子跨平台的边界；最大值为何必须落到最后一个桶。课程的正式提交路径和单独现场检查以助教最新通知为准，不能把 MIT 旧课程的提交地址直接照搬。

现成英文 PDF 已在 [report/lab1-report.pdf](report/lab1-report.pdf)。如果只想从源文件**重新生成相同内容**，在装有 XeLaTeX、`tufte-handout` 类和 Palatino/Helvetica/Menlo 字体的 Mac 上运行下面三行；这是报告排版操作，不能把旧图当成本次复现的现场截图。换成此次复现的新结果时，先更新 [lab1-report.tex](report/lab1-report.tex) 的数值、文字和图像，再编译。

```bash
cd /Users/zzq/Downloads/26秋robotic/26second-seme/lab1/report
xelatex -interaction=nonstopmode -halt-on-error lab1-report.tex
xelatex -interaction=nonstopmode -halt-on-error lab1-report.tex
```
