#!/bin/bash
# One tuning trial in the running simulator (sim, roscore, bridge already up):
#   run_trial.sh <name> <static|circle> <kx> <kv> <kr> <komega> [duration_s]
# Respawns the drone, restarts traj_publisher + controller_node with the given gains,
# records a rosbag and appends the error summary to ~/lab3_work/tuning.txt
set -e
NAME=$1; MODE=$2; KX=$3; KV=$4; KR=$5; KW=$6; DUR=${7:-25}
W=~/lab3_work
source $W/env.sh

# traj_publisher mode is a compile-time switch
TP=~/vnav_ws/src/controller_pkg/src/traj_publisher.cpp
WANT=$([ "$MODE" = static ] && echo 1 || echo 0)
if ! grep -q "^#define STATIC_POSE $WANT" $TP; then
  sed -i "s/^#define STATIC_POSE [01]/#define STATIC_POSE $WANT/" $TP
  (cd ~/vnav_ws && catkin build controller_pkg --no-status 2>&1 | grep -E "error|Summary")
fi

for s in ctrl traj bag; do tmux kill-session -t $s 2>/dev/null || true; done
sleep 1
# respawn: R sent straight to the Unity window (windowactivate does not get focus under WSLg)
SIM=$(xdotool search --name tesse_vnav_scenes | head -1)
xdotool key --window $SIM r
sleep 3

rosparam set /kx $KX; rosparam set /kv $KV; rosparam set /kr $KR; rosparam set /komega $KW
tmux new-session -d -s traj "source $W/env.sh && rosrun controller_pkg traj_publisher > $W/logs/traj.log 2>&1"
tmux new-session -d -s ctrl "source $W/env.sh && rosrun controller_pkg controller_node > $W/logs/ctrl.log 2>&1"
sleep 0.5
rosbag record -q -O $W/bags/$NAME.bag --duration=$DUR /current_state /desired_state /rotor_speed_cmds
{
  echo "=== $NAME  mode=$MODE  kx=$KX kv=$KV kr=$KR komega=$KW"
  python3 $W/analyze_bag.py $W/bags/$NAME.bag --skip ${SKIP:-5} --plot $W/plots/$NAME.png \
    --title "$NAME ($MODE): kx=$KX kv=$KV kr=$KR komega=$KW"
} | tee -a $W/tuning.txt
