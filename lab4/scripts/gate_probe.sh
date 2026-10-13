#!/bin/bash
# Measure how far from the gate centre the drone can fly through gate 0 without
# touching the frame: hover in front of the gate at a lateral (x) or vertical (z)
# offset, fly slowly through the gate plane, and list the collisions.
#   gate_probe.sh x|z <offset> [<offset> ...]
# Gate 0: centre (0.4226, 3.1652, 2.67), yaw -90 deg (flight direction -y).
W=~/lab4_work
source ~/lab3_work/env.sh
AXIS=$1; shift
GX=0.4226; GY=3.1652; GZ=2.67
setpoint() {  # setpoint <x> <y> <z>: hold a static desired state (yaw -90 deg)
  tmux kill-session -t sp 2>/dev/null
  tmux new-session -d -s sp "source ~/lab3_work/env.sh && rostopic pub -r 50 /desired_state trajectory_msgs/MultiDOFJointTrajectoryPoint \"{transforms: [{translation: {x: $1, y: $2, z: $3}, rotation: {x: 0, y: 0, z: -0.7071068, w: 0.7071068}}], velocities: [{}], accelerations: [{}]}\""
}
for s in gen verts bag4 ctrl; do tmux kill-session -t $s 2>/dev/null; done
rosparam set /kx 8; rosparam set /kv 5; rosparam set /kr 10; rosparam set /komega 2
tmux new-session -d -s ctrl "source ~/lab3_work/env.sh && rosrun controller_pkg controller_node > $W/logs/ctrl.log 2>&1"
for off in "$@"; do
  if [ "$AXIS" = x ]; then X=$(echo "$GX + $off" | bc -l); Z=$GZ; else X=$GX; Z=$(echo "$GZ + $off" | bc -l); fi
  setpoint $X 6.0 $Z                       # in front of the gate (it is flown towards -y)
  sleep 9
  timeout 12 rostopic echo /tesse/collision/object_name 2>/dev/null > /tmp/probe_coll.txt &
  setpoint $X 0.5 $Z                       # through the gate plane
  sleep 1.6; import -window $(xdotool search --name tesse_vnav_scenes | head -1) $W/probe_${AXIS}_${off}.png
  sleep 8.4
  wait
  N=$(grep -c "red_square_drone_door" /tmp/probe_coll.txt)
  echo "$AXIS offset $off m: gate-frame collision messages = $N   others: $(grep -v -- --- /tmp/probe_coll.txt | grep -v red_square | sort | uniq -c | tr '\n' ' ')"
done
tmux kill-session -t sp 2>/dev/null
