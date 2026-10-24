#!/bin/bash
# LAB4 race in one command (run inside WSL Ubuntu-20.04, workspace already built):
#   lab4/race.sh [--cruise V] [--runs N] [--record] [--no-rviz]
#   lab4/race.sh --stop
#   --cruise V   cruise speed in m/s (default 14, the configuration of the 6.74 s run)
#   --runs N     fly N races in a row (default 1)
#   --record     also record the Unity view to unity_view.mp4
#   --no-rviz    do not start rviz
#   --stop       shut down the race, rviz, bridge, simulator and roscore
# Gates turn green once passed; close the simulator window to reset them, the next
# run starts a fresh simulator.
# Starts whatever is not running yet (roscore, simulator, bridge, rviz), flies the race
# with the official launch files (traj_following.launch, then traj_gen.launch), prints
# the result and leaves the simulator up for the next run. Results: ~/lab4_runs/<time>/
# Exit status: 0 when every race passed all 12 gates.
set -u
REPO=$(cd "$(dirname "$0")/.." && pwd)
WS=${VNAV_WS:-$HOME/vnav_ws}
SIM_DIR=${VNAV_SIM:-$HOME/vnav-builds/lab4}
OUT_ROOT=${LAB4_RUNS:-$HOME/lab4_runs}
CRUISE=14; RUNS=1; RECORD=0; RVIZ=1; STOP=0
while [ $# -gt 0 ]; do
  case $1 in
    --cruise) CRUISE=$2; shift 2 ;;
    --runs) RUNS=$2; shift 2 ;;
    --record) RECORD=1; shift ;;
    --no-rviz) RVIZ=0; shift ;;
    --stop) STOP=1; shift ;;
    -h|--help) sed -n '2,15p' "$0" | cut -c3-; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
  esac
done

say() { printf '\033[1m[race]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[race] %s\033[0m\n' "$*" >&2; exit 1; }
LOGS=$OUT_ROOT/logs; mkdir -p "$LOGS"
start() {  # start <session> <command>: interactive shell in tmux, output logged
  tmux kill-session -t "$1" 2>/dev/null
  tmux new-session -d -s "$1" -x 200 -y 50
  # the leading space keeps the line out of ~/.bash_history (HISTCONTROL=ignoreboth)
  tmux send-keys -t "$1" " source $WS/devel/setup.bash && export DISPLAY=$DISPLAY && $2 2>&1 | tee $LOGS/$1.log" Enter
}
stop() { tmux send-keys -t "$1" C-c 2>/dev/null; sleep 1; tmux kill-session -t "$1" 2>/dev/null; }
lab4_sim_stop() { stop lab4-sim; pkill -f lab4.x86_64 2> /dev/null; }
wait_for() {  # wait_for <what> <seconds> <command...>  (wall-clock timeout)
  local what=$1 end=$((SECONDS + $2)); shift 2
  while [ $SECONDS -lt $end ]; do "$@" > /dev/null 2>&1 && return 0; sleep 1; done
  die "timed out waiting for $what"
}
master_up() { timeout 3 rosnode list > /dev/null 2>&1; }
odom_once() {  # one /current_state sample as "x y z", or fail
  python3 - "$@" << 'EOF'
import sys, rospy
from nav_msgs.msg import Odometry
rospy.init_node("race_probe", anonymous=True, disable_signals=True)
p = rospy.wait_for_message("/current_state", Odometry, timeout=3).pose.pose.position
print(p.x, p.y, p.z)
EOF
}
at_spawn() { read -r x y z <<< "$(odom_once)" && python3 -c "import sys; x,y,z=map(float,sys.argv[1:]); sys.exit(not (abs(x-0.4)<0.3 and abs(y-8)<0.3 and z<0.3))" "$x" "$y" "$z"; }
stop_bag() {  # let rosbag finish writing the index before the session goes away
  tmux send-keys -t lab4-bag C-c 2> /dev/null
  [ -n "${DIR:-}" ] && wait_for "the rosbag to close" 15 test -f "$DIR/race.bag"
  tmux kill-session -t lab4-bag 2> /dev/null
}
stop_rotors() { timeout 5 rostopic pub -1 /rotor_speed_cmds mav_msgs/Actuators "{angular_velocities: [0, 0, 0, 0]}" > /dev/null 2>&1; }

# ---- preflight -------------------------------------------------------------
export DISPLAY=${DISPLAY:-:0}
[ -f "$WS/devel/setup.bash" ] || die "workspace not built: cd $WS && catkin build"
set +u; source "$WS/devel/setup.bash"; set -u   # ROS setup scripts read unset variables
for c in tmux xdotool xwininfo python3; do command -v $c > /dev/null || die "missing command: $c"; done
[ $RECORD = 0 ] || { command -v ffmpeg > /dev/null && command -v import > /dev/null; } || die "--record needs ffmpeg and imagemagick"

if [ $STOP = 1 ]; then
  for s in lab4-gates lab4-follow lab4-bag; do stop $s; done
  master_up && stop_rotors
  for s in lab4-rviz lab4-relay lab4-bridge lab4-sim lab4-core; do stop $s; done
  say "stopped"; exit 0
fi

[ -x "$SIM_DIR/lab4.x86_64" ] || die "simulator not found in $SIM_DIR (vnav.mit.edu/material/lab4.zip)"
case $(readlink -f "$(rospack find trajectory_generation)") in
  "$REPO"/*) ;; *) say "warning: trajectory_generation is not built from $REPO" ;;
esac
BRIDGE=$(rospack find tesse_ros_bridge)/src/tesse_ros_bridge
grep -q "sim time went back" "$BRIDGE/tesse_ros_node.py" || {
  say "patching tesse_ros_node.py (simulator clock reset)"
  python3 "$REPO/lab4/scripts/patch_bridge.py" "$BRIDGE/tesse_ros_node.py"; }
sed -i '1s|^#!/usr/bin/env python$|#!/usr/bin/env python3|' "$BRIDGE/tesse_ros_node.py" "$BRIDGE/quadrotor_control_interface.py"

# ---- bring-up (only what is not running) ------------------------------------
tmux ls 2> /dev/null | grep -q ^lab3- && "$REPO/lab3/circle.sh" stop   # LAB3 leftovers would keep publishing the circle
if ! master_up; then say "starting roscore"; start lab4-core roscore; wait_for "roscore" 30 master_up; fi
# Probing which OpenGL version it can use crashes the Unity player under WSLg most of
# the time ("[xcb] Unknown sequence number while processing queue"), ~1.5 s after its
# window appears; asking for the 3.3 core profile it ends up with avoids that
SIM_STARTED=0   # closing the simulator window resets the gates (they turn green once passed)
for attempt in 1 2 3; do
  pgrep -f lab4.x86_64 > /dev/null && break
  say "starting the simulator"
  SIM_STARTED=1
  start lab4-sim "cd $SIM_DIR && env -u LIBGL_ALWAYS_SOFTWARE ./lab4.x86_64 -force-gfx-direct -force-glcore33 -screen-fullscreen 0 -screen-width 1024 -screen-height 768"
  wait_for "the simulator window" 60 xdotool search --name tesse_vnav_scenes
  sleep 5
  pgrep -f lab4.x86_64 > /dev/null || say "the simulator crashed during start-up (attempt $attempt), see $LOGS/lab4-sim.log"
done
pgrep -f lab4.x86_64 > /dev/null || die "the simulator does not start, see ~/.config/unity3d/DefaultCompany/tesse_vnav_scenes/Player.log"
SIMWIN=$(xdotool search --name tesse_vnav_scenes | head -1)
# WSLg only has a real display when the WSL VM was started from the Windows desktop;
# started from SSH it gets a 640x480 dummy screen and Unity exits shortly after
xwininfo -id "$SIMWIN" | grep -q IsViewable || { lab4_sim_stop; die "the simulator window is not on the Windows desktop.
  WSL was started without the desktop session. In Windows run:  wsl --shutdown
  then open Ubuntu-20.04 from the Start menu and run this script again"; }
# WSLg now and then keeps a new window hidden on the Windows desktop while X sees it
# mapped; mapping it again makes Windows create it afresh, in front (moved back to the
# top-left corner, as every remap shifts it by the 32 px shadow margin)
xdotool windowunmap --sync "$SIMWIN"; xdotool windowmap --sync "$SIMWIN"; xdotool windowmove "$SIMWIN" 0 0
# a new simulator needs the bridge's start-up handshake (scene change) again
if [ $SIM_STARTED = 1 ] && rosnode list 2> /dev/null | grep -q tesse_ros_bridge; then
  say "restarting the bridge for the new simulator"
  stop lab4-bridge
  rosnode kill /tesse/tesse_ros_bridge /tesse/quadrotor_control_interface > /dev/null 2>&1
  echo y | rosnode cleanup > /dev/null 2>&1
fi
if ! rosnode list 2> /dev/null | grep -q tesse_ros_bridge; then
  say "starting the bridge"
  start lab4-bridge "roslaunch tesse_ros_bridge tesse_quadrotor_bridge.launch publish_collisions:=true"
fi
pgrep -f lab4.x86_64 > /dev/null || die "the simulator exited, see $LOGS/lab4-sim.log"
wait_for "/current_state from the bridge" 60 odom_once
if [ $RVIZ = 1 ] && ! pgrep -x rviz > /dev/null; then
  say "starting rviz"
  start lab4-relay "python3 $REPO/lab4/scripts/gate_relay.py"
  start lab4-rviz "rviz -d $REPO/lab4/rviz/lab4_topview.rviz"
fi

# ---- races --------------------------------------------------------------------
IN_RACE=0
cleanup_race() {  # on any exit during a race: stop recording and the race nodes, rotors off
  [ "$IN_RACE" = 1 ] || return 0
  IN_RACE=0
  touch "$DIR/.stop_capture"
  stop_bag; stop lab4-gates; stop lab4-follow; stop_rotors
  say "race aborted: recording and race nodes stopped, rotors off"
}
trap cleanup_race EXIT
trap 'exit 130' INT TERM
FAILED=0
for run in $(seq 1 "$RUNS"); do
  DIR=$OUT_ROOT/$(date +%Y%m%d-%H%M%S)_c$CRUISE; mkdir -p "$DIR"
  say "run $run/$RUNS, cruise $CRUISE m/s -> $DIR"
  IN_RACE=1
  stop lab4-gates; stop lab4-follow; stop lab4-bag; stop_rotors
  for k in 1 2 3; do xdotool key --window "$SIMWIN" r; sleep 3; at_spawn && break; done
  at_spawn || die "the drone did not respawn at the start pad"
  rosparam delete /trajectory_generation_node 2> /dev/null   # leftovers from manual runs
  start lab4-follow "stdbuf -oL -eL roslaunch trajectory_generation traj_following.launch cruise:=$CRUISE"
  wait_for "trajectory_generation_node" 30 bash -c "rosnode list | grep -q trajectory_generation_node"
  start lab4-bag "rosbag record -O $DIR/race.bag /current_state /desired_state /desired_traj_vertices /rotor_speed_cmds /tesse/collision /tf"
  sleep 2
  if [ $RECORD = 1 ]; then
    ( while [ ! -f "$DIR/.stop_capture" ]; do import -window "$SIMWIN" ppm:-; done ) | ffmpeg -nostdin -y -loglevel error \
      -f image2pipe -c:v ppm -use_wallclock_as_timestamps 1 -i - -vf format=yuv420p -r 15 -c:v libx264 -crf 23 "$DIR/unity_view.mp4" &
  fi
  start lab4-gates "stdbuf -oL -eL roslaunch planner_pkg traj_gen.launch"
  wait_for "the trajectory" 30 grep -q "duration" "$LOGS/lab4-follow.log"
  DUR=$(grep -o "duration [0-9.]*" "$LOGS/lab4-follow.log" | tail -1 | cut -d' ' -f2)
  say "trajectory planned: $DUR s, flying"
  sleep "$(python3 -c "print($DUR + 2)")"
  touch "$DIR/.stop_capture"; wait; rm -f "$DIR/.stop_capture"
  stop_bag; stop lab4-gates
  IN_RACE=0
  { echo "commit: $(git -C "$REPO" describe --always --dirty)"; echo "cruise: $CRUISE"; echo "date: $(date)"
    for k in kx kv kr komega use_omega_d; do echo "$k: $(rosparam get /$k)"; done; } > "$DIR/params.txt"
  cp "$LOGS/lab4-follow.log" "$DIR/traj_following.log"
  python3 "$REPO/lab4/scripts/race_check.py" "$DIR/race.bag" --plot "$DIR/race.png" --title "cruise $CRUISE m/s" > "$DIR/summary.txt" 2>&1
  grep -E "gates passed|race time|max speed|airborne" "$DIR/summary.txt" | sed 's/^/        /'
  grep -q "passed in order: 12/12" "$DIR/summary.txt" || FAILED=1
done
say "done; the drone hovers at the exit point, simulator left running (lab4/race.sh --stop to shut down)"
exit $FAILED
