#!/usr/bin/env bash
set -euo pipefail

output=/home/qz/lab1/fortunes.txt
if [[ -e "$output" ]]; then
  echo "Refusing to replace existing $output" >&2
  exit 1
fi

: > "$output"
for n in 1 2 3 4 5; do
  /usr/games/fortune >> "$output"
  printf 'append %d: %s bytes total\n' "$n" "$(wc -c < "$output")"
done
