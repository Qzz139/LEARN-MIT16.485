#!/bin/bash
# LAB3 circle in one command (WSL Ubuntu-20.04, workspace built):  lab3/circle.sh  |  lab3/circle.sh stop
# Starts what is not running (roscore, simulator, bridge, rviz), respawns the drone, flies the circle
# with traj_tracking.launch, records 40 s after 15 s of settling and prints tracking error, yaw lag
# and smoothness; the drone keeps circling. Results: ~/lab3_runs/<time>/
R=$(cd "$(dirname "$0")/.." && pwd); OUT=~/lab3_runs; mkdir -p $OUT
source ~/vnav_ws/devel/setup.bash; export DISPLAY=${DISPLAY:-:0}
start() { tmux kill-session -t $1 2>/dev/null; tmux new-session -d -s $1; tmux send-keys -t $1 " source ~/vnav_ws/devel/setup.bash && $2 2>&1 | tee $OUT/$1.log" Enter; }
stop() { tmux send-keys -t $1 C-c 2>/dev/null; sleep 1; tmux kill-session -t $1 2>/dev/null; }
off() { timeout 5 rostopic pub -1 /rotor_speed_cmds mav_msgs/Actuators "{angular_velocities: [0, 0, 0, 0]}" >/dev/null 2>&1; }
until_ok() { local end=$((SECONDS + $1)); shift; until "$@" >/dev/null 2>&1; do [ $SECONDS -lt $end ] || { echo "timed out: $*"; exit 1; }; sleep 1; done; }
if [[ $1 == *stop ]]; then stop lab3-fly; off; for s in lab3-rviz lab3-bridge lab3-sim lab3-core; do stop $s; done; pkill -f lab3.x86_64; exit; fi
tmux ls 2>/dev/null | grep -q ^lab4- && $R/lab4/race.sh --stop   # LAB4 leftovers (roscore, bridge, trajectory node) would hijack the circle
pgrep -f lab4.x86_64 >/dev/null && { echo "the LAB4 simulator uses the same ports: lab4/race.sh --stop first"; exit 1; }
rosnode list >/dev/null 2>&1 || { start lab3-core roscore; until_ok 30 rosnode list; }
NEW=0; pgrep -f lab3.x86_64 >/dev/null || { NEW=1; start lab3-sim "cd ~/vnav-builds/lab3 && env -u LIBGL_ALWAYS_SOFTWARE ./lab3.x86_64 -force-glcore33"; }
# wait for a visible window of the lab3 process (the LAB4 window has the same title, so search by class)
for i in $(seq 60); do W=; for w in $(xdotool search --class lab3.x86_64); do xwininfo -id $w | grep -q IsViewable && W=$w; done; [ -n "$W" ] && break; sleep 1; done
[ -n "$W" ] || { echo "no simulator window on the Windows desktop: in Windows run wsl --shutdown, open Ubuntu-20.04 from the Start menu, retry"; exit 1; }
xdotool windowunmap --sync $W; xdotool windowmap --sync $W; xdotool windowmove $W 0 0   # WSLg sometimes hides new windows
[ $NEW = 1 ] && stop lab3-bridge   # a new simulator needs a fresh bridge
rosnode list | grep -q tesse_ros_bridge || start lab3-bridge "roslaunch tesse_ros_bridge tesse_quadrotor_bridge.launch"
until_ok 60 timeout 3 rostopic echo -n1 /current_state
pgrep -x rviz >/dev/null || start lab3-rviz "rviz -d $R/lab3/controller_pkg/rviz/lab3_topview.rviz"
D=$OUT/$(date +%Y%m%d-%H%M%S); mkdir -p $D
trap 'stop lab3-fly; off; exit 130' INT
stop lab3-fly; off; xdotool key --window $W r; sleep 3   # rotors off first: the simulator keeps the last command
start lab3-fly "roslaunch controller_pkg traj_tracking.launch"
sleep 15; rosbag record -q -O $D/circle.bag --duration=40 /current_state /desired_state /rotor_speed_cmds /tf
cd $R/lab3/scripts && { python3 analyze_bag.py $D/circle.bag --plot $D/circle.png; python3 jitter_check.py $D/circle.bag --skip 0; python3 yaw_plot.py $D/circle.bag $D/yaw.png; } > $D/summary.txt 2>&1
grep -E "position error|yaw error|jitter|base_link_gt" $D/summary.txt; echo "results in $D; the drone keeps circling (lab3/circle.sh stop to shut down)"
