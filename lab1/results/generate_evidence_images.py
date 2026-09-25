#!/usr/bin/env python3
"""Render freshly verified SSH/WSL command output as report figures.

These are rendered command transcripts, not photographs of a desktop window.
"""

from datetime import datetime
from pathlib import Path
import subprocess
import textwrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures"
SOCKET = "/private/tmp/codex-wsl-zzq/master.sock"
HOST = "qz@100.84.51.48"
FONT = "/System/Library/Fonts/Menlo.ttc"


def run(command: str) -> str:
    # Commands here are fixed by this script and use no user-provided input.
    remote = f'wsl.exe --distribution Ubuntu-20.04 --exec bash -lc "{command}"'
    result = subprocess.run(
        ["ssh", "-S", SOCKET, "-o", "BatchMode=yes", HOST, remote],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\n{result.stderr}")
    return result.stdout.replace("\r", "").rstrip()


def render(slug: str, title: str, steps: list[tuple[str, str]]) -> None:
    lines = []
    for label, command in steps:
        output = run(command)
        lines.append(f"$ {label}")
        lines.extend(output.splitlines() or ["(no output; exit status 0)"])
        lines.append("")

    OUT.mkdir(exist_ok=True)
    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    transcript = (
        f"{title}\nSource: live SSH to {HOST}, Ubuntu-20.04 WSL2\nCaptured: {timestamp}\n\n"
        + "\n".join(lines).rstrip()
        + "\n"
    )
    (OUT / f"{slug}.txt").write_text(transcript, encoding="utf-8")

    mono = ImageFont.truetype(FONT, 22)
    head = ImageFont.truetype(FONT, 27)
    small = ImageFont.truetype(FONT, 17)
    pad = 40
    line_height = 32
    width = 1520
    usable = width - 2 * pad
    wrapped = []
    for line in lines:
        if len(line) <= 103:
            wrapped.append(line)  # Keep leading spaces in histogram rows.
        else:
            wrapped.extend(textwrap.wrap(line, width=103, break_long_words=True,
                                         break_on_hyphens=False, drop_whitespace=False))
    height = 150 + line_height * len(wrapped) + 54
    image = Image.new("RGB", (width, height), "#111827")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 104), fill="#1f2937")
    draw.text((pad, 23), title, font=head, fill="#f9fafb")
    draw.text((pad, 63), f"Ubuntu-20.04 / {timestamp}", font=small, fill="#9ca3af")
    y = 127
    for line in wrapped:
        if line.startswith("$ "):
            color = "#7dd3fc"
        elif "(no output" in line:
            color = "#a7f3d0"
        else:
            color = "#e5e7eb"
        draw.text((pad, y), line, font=mono, fill=color)
        y += line_height
    draw.line((pad, height - 43, width - pad, height - 43), fill="#374151", width=1)
    draw.text(
        (pad, height - 33),
        "Rendered from live command output; not a desktop screenshot. Full transcript saved alongside.",
        font=small,
        fill="#9ca3af",
    )
    image.save(OUT / f"{slug}.png")
    print(OUT / f"{slug}.png")


render(
    "01_ubuntu_environment",
    "Lab 1 · Ubuntu installation and setup",
    [
        ("cat /etc/os-release | grep -E 'PRETTY_NAME|VERSION_ID|VERSION_CODENAME'", "cat /etc/os-release | grep -E 'PRETTY_NAME|VERSION_ID|VERSION_CODENAME'"),
        ("uname -m; id", "uname -m; id"),
        ("dpkg-query -W build-essential cmake git", "dpkg-query -W build-essential cmake git"),
        ("g++ --version | head -n 1; cmake --version | head -n 1", "g++ --version | head -n 1; cmake --version | head -n 1"),
    ],
)

render(
    "02_compile_examples",
    "Lab 1 · Compile and run examples",
    [
        ("g++ -std=c++11 -Wall -Wextra -pedantic /home/qz/lab1/examples/hello.cpp -o /home/qz/lab1/examples/hello", "g++ -std=c++11 -Wall -Wextra -pedantic /home/qz/lab1/examples/hello.cpp -o /home/qz/lab1/examples/hello"),
        ("/home/qz/lab1/examples/hello", "/home/qz/lab1/examples/hello"),
        ("cmake --build /home/qz/lab1/examples/cmake-example/build", "cmake --build /home/qz/lab1/examples/cmake-example/build"),
        ("/home/qz/lab1/examples/cmake-example/build/example", "/home/qz/lab1/examples/cmake-example/build/example"),
    ],
)

render(
    "03_shell_operations",
    "Lab 1 · Shell operations",
    [
        ("wc -l -w /home/qz/lab1/data/dante.txt", "wc -l -w /home/qz/lab1/data/dante.txt"),
        ("grep -cve '^[[:space:]]*$' /home/qz/lab1/data/dante.txt", "grep -cve '^[[:space:]]*$' /home/qz/lab1/data/dante.txt"),
        ("sed -n '9,13p' /home/qz/lab1/append_fortunes.sh", "sed -n '9,13p' /home/qz/lab1/append_fortunes.sh"),
        ("wc -c /home/qz/lab1/fortunes.txt; sha256sum /home/qz/lab1/fortunes.txt", "wc -c /home/qz/lab1/fortunes.txt; sha256sum /home/qz/lab1/fortunes.txt"),
    ],
)

render(
    "04_cpp_warmup",
    "Lab 1 · C++ warm-up verification",
    [
        ("/home/qz/lab1/results/cpp_warmup_check", "/home/qz/lab1/results/cpp_warmup_check"),
    ],
)

render(
    "05_random_vector",
    "Lab 1 · RandomVector practice",
    [
        ("/home/qz/lab1/RandomVector/random_vector", "/home/qz/lab1/RandomVector/random_vector"),
        ("/home/qz/lab1/RandomVector/test_random_vector", "/home/qz/lab1/RandomVector/test_random_vector"),
    ],
)
