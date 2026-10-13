#!/bin/bash
# Generate the race trajectory without flying, to inspect the optimiser quickly:
#   gen_only.sh <v_max> <a_max> [nonlinear true|false] [time_penalty] [time_alloc_method] [print_debug] [time_mode]
# EXIT and SF env vars set the exit distance and take-off factor.
# Needs the simulator + bridge (for the start pose); no controller is started.
W=~/lab4_work
source ~/lab3_work/env.sh
for s in gen ctrl verts bag4; do tmux kill-session -t $s 2>/dev/null; done
# respawn so the plan starts from the spawn point, as in a race
xdotool key --window $(xdotool search --name tesse_vnav_scenes | head -1) r; sleep 3
rosparam set /trajectory_generation_node/v_max $1
rosparam set /trajectory_generation_node/a_max $2
rosparam set /trajectory_generation_node/nonlinear ${3:-true}
rosparam set /trajectory_generation_node/time_penalty ${4:-500}
rosparam set /trajectory_generation_node/time_alloc_method ${5:-3}
rosparam set /trajectory_generation_node/print_debug ${6:-false}
rosparam set /trajectory_generation_node/time_mode ${7:-0}
rosparam set /trajectory_generation_node/exit_distance ${EXIT:-0}
rosparam set /trajectory_generation_node/start_factor ${SF:-2.0}
rosparam delete /trajectory_generation_node/segment_scale 2>/dev/null || true
[ -n "$SEG" ] && rosparam set /trajectory_generation_node/segment_scale "$SEG"
tmux new-session -d -s gen "source ~/lab3_work/env.sh && stdbuf -oL -eL rosrun trajectory_generation trajectory_generation_node > $W/logs/gen_only.log 2>&1"
sleep 2
tmux new-session -d -s verts "source ~/lab3_work/env.sh && roslaunch planner_pkg traj_gen.launch > /dev/null 2>&1"
for i in $(seq 1 60); do grep -q "Generated" $W/logs/gen_only.log && break; sleep 1; done
tmux kill-session -t verts 2>/dev/null; tmux kill-session -t gen 2>/dev/null
grep -E "Segment times|nlopt|Generated|Plan:" $W/logs/gen_only.log | sed 's/\x1b\[[0-9;]*m//g; s/^\[INFO\] \[[0-9., ]*\]: //'
