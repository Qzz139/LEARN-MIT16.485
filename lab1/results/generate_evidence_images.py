#!/usr/bin/env python3
"""Run commands in the WSL Ubuntu-20.04 over SSH and render their output as report figures.

These are rendered command transcripts, not photographs of a desktop window.
Needs the shared SSH socket (see SOCKET). Render all figures, or only the named ones:
    python3 lab1/results/generate_evidence_images.py [05_random_vector ...]
"""

from datetime import datetime
from pathlib import Path
import subprocess
import sys
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


def render(slug: str, title: str, commands: list[str]) -> None:
    lines = []
    for command in commands:
        output = run(command)
        lines.append(f"$ {command}")
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


L = "/home/qz/lab1"  # lab1 copy inside WSL

FIGURES = {
    "01_ubuntu_environment": ("Lab 1 · Ubuntu installation and setup", [
        "cat /etc/os-release | grep -E 'PRETTY_NAME|VERSION_ID|VERSION_CODENAME'",
        "uname -m; id",
        "dpkg-query -W build-essential cmake git",
        "g++ --version | head -n 1; cmake --version | head -n 1",
    ]),
    "02_compile_examples": ("Lab 1 · Compile and run examples", [
        f"g++ -std=c++11 -Wall -Wextra -pedantic {L}/examples/hello.cpp -o {L}/examples/hello",
        f"{L}/examples/hello",
        f"cmake --build {L}/examples/cmake-example/build",
        f"{L}/examples/cmake-example/build/example",
    ]),
    "03_shell_operations": ("Lab 1 · Shell operations", [
        f"wc -l -w {L}/data/dante.txt",
        f"grep -cve '^[[:space:]]*$' {L}/data/dante.txt",
        f"sed -n '9,13p' {L}/append_fortunes.sh",
        f"wc -c {L}/fortunes.txt; sha256sum {L}/fortunes.txt",
    ]),
    "04_cpp_warmup": ("Lab 1 · C++ warm-up verification", [
        f"{L}/results/cpp_warmup_check",
    ]),
    "05_random_vector": ("Lab 1 · RandomVector practice", [
        f"{L}/RandomVector/random_vector",
        f"{L}/RandomVector/test_random_vector",
    ]),
}

if __name__ == "__main__":
    for slug in sys.argv[1:] or FIGURES:
        render(slug, *FIGURES[slug])
