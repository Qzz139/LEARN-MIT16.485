#!/bin/bash
# One race in the running lab4 simulator (sim, roscore and bridge already up):
#   [OMD=1] [SEG="[..]"] [NL=1] [TP=time_penalty] [TM=time_mode] [EXIT=m] [SF=start_factor] run_race.sh <name> [v_max] [a_max] [kx kv kr komega] [duration_s]
# NL=1 switches the trajectory generator to the nonlinear (time-optimised) solver.
# Respawns the drone, starts trajectory_generation_node + controller_node, records a
# rosbag, publishes the gates (which triggers trajectory generation) and summarises.
set -e
NAME=$1; VMAX=${2:-8}; AMAX=${3:-4}
KX=${4:-8}; KV=${5:-5}; KR=${6:-10}; KW=${7:-2}; DUR=${8:-35}
W=~/lab4_work
source ~/lab3_work/env.sh
mkdir -p $W/bags $W/plots

for s in gen ctrl verts bag4; do tmux kill-session -t $s 2>/dev/null || true; done
# the simulator keeps applying the last rotor command it got: stop the rotors
# first, otherwise a stale (possibly chattering) command shoves the respawned drone
rostopic pub -1 /rotor_speed_cmds mav_msgs/Actuators "{angular_velocities: [0, 0, 0, 0]}" > /dev/null 2>&1
SIM=$(xdotool search --name tesse_vnav_scenes | head -1)
for k in 1 2 3; do
  xdotool key --window $SIM r
  sleep 3
  POS=$(timeout 3 rostopic echo -n1 /current_state/pose/pose/position 2>/dev/null | awk '/x:|y:|z:/{printf "%s ", $2}')
  if python3 -c "import sys; x,y,z=map(float,sys.argv[1:4]); sys.exit(0 if abs(x-0.4)<0.3 and abs(y-8.0)<0.3 and z<0.3 else 1)" $POS; then
    break
  fi
  echo "respawn check failed (pos: $POS), retrying"
done

rosparam set /kx $KX; rosparam set /kv $KV; rosparam set /kr $KR; rosparam set /komega $KW
rosparam set /use_omega_d $([ "${OMD:-0}" = 1 ] && echo true || echo false)
rosparam set /trajectory_generation_node/v_max $VMAX
rosparam set /trajectory_generation_node/a_max $AMAX
rosparam set /trajectory_generation_node/nonlinear $([ "${NL:-0}" = 1 ] && echo true || echo false)
rosparam set /trajectory_generation_node/time_penalty ${TP:-500}
rosparam set /trajectory_generation_node/time_mode ${TM:-0}
rosparam set /trajectory_generation_node/exit_distance ${EXIT:-0}
rosparam set /trajectory_generation_node/start_factor ${SF:-2.0}
rosparam delete /trajectory_generation_node/segment_scale 2>/dev/null || true
[ -n "$SEG" ] && rosparam set /trajectory_generation_node/segment_scale "$SEG"
tmux new-session -d -s ctrl "source ~/lab3_work/env.sh && rosrun controller_pkg controller_node > $W/logs/ctrl.log 2>&1"
tmux new-session -d -s gen "source ~/lab3_work/env.sh && stdbuf -oL -eL rosrun trajectory_generation trajectory_generation_node > $W/logs/gen.log 2>&1"
sleep 2
tmux new-session -d -s bag4 "source ~/lab3_work/env.sh && rosbag record -q -O $W/bags/$NAME.bag --duration=$DUR /current_state /desired_state /desired_traj_vertices /rotor_speed_cmds /tesse/collision"
sleep 1
tmux new-session -d -s verts "source ~/lab3_work/env.sh && roslaunch planner_pkg traj_gen.launch > $W/logs/verts.log 2>&1"
sleep $((DUR + 3))
tmux kill-session -t verts 2>/dev/null || true
{
  echo "=== $NAME  omd=${OMD:-0} seg=${SEG:-none} exit=${EXIT:-0} sf=${SF:-2.0} time_mode=${TM:-0} nonlinear=${NL:-0} tp=${TP:-500} v_max=$VMAX a_max=$AMAX  kx=$KX kv=$KV kr=$KR komega=$KW"
  grep -E "Generated|Plan:" $W/logs/gen.log | sed "s/\x1b\[[0-9;]*m//g; s/^\[INFO\] \[[0-9., ]*\]: //" | head -2
  python3 $W/race_check.py $W/bags/$NAME.bag --plot $W/plots/$NAME.png --title "$NAME: v_max=$VMAX a_max=$AMAX gains $KX/$KV/$KR/$KW"
} | tee -a $W/races.txt
