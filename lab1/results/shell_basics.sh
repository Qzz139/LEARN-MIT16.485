#!/usr/bin/env bash
set -euo pipefail

work=/home/qz/lab1/shell-demo
mkdir -p "$work"
cd "$work"
printf 'shell practice\n' > original.txt
cp original.txt copy.txt
mv copy.txt renamed.txt
chmod 640 renamed.txt

printf 'working directory: '
pwd
printf 'files: '
find . -maxdepth 1 -type f -printf '%f ' | sort
printf 'renamed file permissions: '
stat -c '%a' renamed.txt
printf 'word count through a pipe: '
cat renamed.txt | wc -w
