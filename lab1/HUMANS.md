# Lab 1 手操复现说明

环境：Windows 主机上的 WSL 2 / Ubuntu-20.04.6（用户 `qz`）。除标明 PowerShell 的命令外，都在 Ubuntu 的 Bash 里运行。参照值来自 2026-09-24 的记录。日期、`fortune` 的内容、其他 C 库上的随机数都可能不同，不要冒充原始截图。报告见 [lab1-report.pdf](report/lab1-report.pdf)，思路见 [PLAN.md](PLAN.md)。

| 给分点 | 节 | 证据 |
| --- | --- | --- |
| 安装 Ubuntu 并完成配置（40） | §0、§1 | [environment.txt](results/environment.txt) |
| 编译示例代码（5） | §2 | [compile_examples.txt](results/compile_examples.txt) |
| Shell 操作（5） | §3 | [shell.txt](results/shell.txt)、[exercise1.txt](exercise1.txt)、[fortunes.txt](fortunes.txt) |
| C++ 问答（25） | §4 | [cpp-warmup.txt](cpp-warmup.txt)、[cpp_warmup_check.txt](results/cpp_warmup_check.txt) |
| C++ 实践（25） | §5 | [random_vector.txt](results/random_vector.txt)、[random_vector_validation.txt](results/random_vector_validation.txt) |

## 0. 安装与进入 Ubuntu

已有发行版时，在 PowerShell 里运行 `wsl.exe --distribution Ubuntu-20.04`。主机上还有另一个名为 `Ubuntu` 的发行版，**不要只输入 `wsl`**。

新主机的安装方法（PowerShell）：

```powershell
wsl.exe --update
$Image = Join-Path $env:USERPROFILE 'Downloads\ubuntu-20.04.6-wsl-amd64.wsl'
curl.exe -L --fail --output $Image https://releases.ubuntu.com/focal/ubuntu-20.04.6-wsl-amd64.wsl
(Get-FileHash $Image -Algorithm SHA256).Hash.ToLower()
wsl.exe --install --from-file $Image
```

第 4 行算出的哈希值必须是 `a9073f3726aab9661076506603706eadf284b80a791dec3adfde8e1989906fa4`，不一致就停止安装。安装完成后首次启动，按提示建立用户 `qz`。

进入 Ubuntu 后，安装工具并准备一个独立的工作副本，后面的操作都只影响这个副本：

```bash
sudo apt-get update && sudo apt-get install -y build-essential cmake git curl fortune-mod fortunes-min
cd ~ && git clone https://github.com/Qzz139/26second-seme.git
mkdir -p ~/lab1-replay && cp -a ~/26second-seme/lab1/. ~/lab1-replay/ && cd ~/lab1-replay && mkdir -p results/replay
```

## 1. Ubuntu 配置证据（40）

```bash
cat /etc/os-release | tee results/replay/os-release.txt
uname -m; id; g++ --version | head -1; cmake --version | head -1; git --version
g++ -std=c++11 -Wall -Wextra -pedantic results/toolchain_smoke.cpp -o results/replay/toolchain_smoke && ./results/replay/toolchain_smoke
```

**应看到**：

- `VERSION_ID="20.04"`，架构 `x86_64`，用户 `qz` 在 sudo 组；
- 版本为 g++ 9.4.0、CMake 3.16.3，补丁版本可以不同；
- 最后一行输出 `Ubuntu 20.04 toolchain OK`。

截图时显示终端窗口，按 Win+Shift+S 截取。

## 2. 编译示例代码（5）

```bash
g++ -std=c++11 -Wall -Wextra -pedantic examples/hello.cpp -o results/replay/hello && ./results/replay/hello
cmake -S examples/cmake-example -B results/replay/cmake-build && cmake --build results/replay/cmake-build && ./results/replay/cmake-build/example
```

**应看到**：第一条输出 `Hello from Lab 1 on Ubuntu 20.04!`；第二条输出 `CMake library link OK`（库和可执行文件分开编译，再链接到一起）。

## 3. Shell 操作（5）

```bash
LC_ALL=C wc -l -w data/dante.txt
LC_ALL=C grep -cve '^[[:space:]]*$' data/dante.txt
: > fortunes.txt; for i in 1 2 3 4 5; do /usr/games/fortune >> fortunes.txt; done; cat fortunes.txt
mkdir -p shell-demo && cd shell-demo && printf 'shell practice\n' > original.txt && cp original.txt copy.txt && mv copy.txt renamed.txt && chmod 640 renamed.txt && stat -c '%a' renamed.txt && cat renamed.txt | wc -w && cd ..
```

**应看到**：

- **Dante 文本统计**：19567 行、97676 词、14338 个非空行（文件 557042 字节）。题目答案见 [exercise1.txt](exercise1.txt)。
- **fortune**：调用 5 次，每次追加到 `fortunes.txt`，中间不能用 `>` 覆盖。
- **最后一行**：演示建目录、复制、移动、`chmod 640` 改权限和管道的用法，应输出权限 `640` 和单词数 `2`。仓库里的 [shell_basics.sh](results/shell_basics.sh) 做的是同样的事，但工作目录写死成了 `/home/qz/lab1/shell-demo`。

## 4. C++ 问答（25）

```bash
g++ -std=c++11 -Wall -Wextra -pedantic results/cpp_warmup_check.cpp -o results/replay/cpp_warmup_check && ./results/replay/cpp_warmup_check
```

**应看到**：输出与 [cpp_warmup_check.txt](results/cpp_warmup_check.txt) 一致：

```
O1 i=2 j=1
O2 b
R1 10 10
R2 1764
R3 0
R4 0
N1 sizeof(short,int,long,long long)=2,4,8,8
N2 sizeof(float,double)=4,8 i=3
N3 c=255
N4 i=0
```

各题的文字答案见 [cpp-warmup.txt](cpp-warmup.txt)。

## 5. C++ 实践：RandomVector（25）

```bash
g++ -std=c++11 -Wall -Wextra -pedantic RandomVector/main.cpp RandomVector/random_vector.cpp -o results/replay/random_vector && ./results/replay/random_vector
g++ -std=c++11 -Wall -Wextra -pedantic RandomVector/test_random_vector.cpp RandomVector/random_vector.cpp -o results/replay/test_random_vector && ./results/replay/test_random_vector
```

**应看到**：

- **主程序**（种子 314159）：`Mean: 0.55804`、`Min: 0.0278694`、`Max: 0.982655`，5 个直方图桶的计数为 5 1 4 3 7，合计 20。判断是否正确，看三点即可：`min ≤ mean ≤ max`、计数加起来是 20、程序没有崩溃。
- **测试程序**：输出 `All RandomVector checks passed: ...`，涵盖取值范围、1/5/30 个桶的计数守恒、全部取值相等这几种情况。
- **代码**：在 [RandomVector](RandomVector/) 目录。

## 6. 报告

```bash
cd ~/26second-seme/lab1/report && xelatex lab1-report.tex && xelatex lab1-report.tex
```

在装有 TeX 的机器上运行，比如 Mac。
