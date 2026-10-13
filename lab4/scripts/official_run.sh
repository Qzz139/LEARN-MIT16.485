#!/bin/bash
# Race with the official launch files and collect the evidence:
#   official_run.sh <name>
# roslaunch trajectory_generation traj_following.launch, then
# roslaunch planner_pkg traj_gen.launch (as in the handout), while recording a rosbag,
# the Unity view, the ROS graph and topic information.
W=~/lab4_work
O=$W/official/$1
source ~/lab3_work/env.sh
mkdir -p $O
for s in gen ctrl verts bag4 follow; do tmux kill-session -t $s 2>/dev/null; done
rostopic pub -1 /rotor_speed_cmds mav_msgs/Actuators "{angular_velocities: [0, 0, 0, 0]}" > /dev/null 2>&1
SIM=$(xdotool search --name tesse_vnav_scenes | head -1)
for k in 1 2 3; do
  xdotool key --window $SIM r; sleep 3
  POS=$(timeout 3 rostopic echo -n1 /current_state/pose/pose/position 2>/dev/null | awk '/x:|y:|z:/{printf "%s ", $2}')
  python3 -c "import sys; x,y,z=map(float,sys.argv[1:4]); sys.exit(0 if abs(x-0.4)<0.3 and abs(y-8.0)<0.3 and z<0.3 else 1)" $POS && break
done
# parameters left over from the tuning runs would override nothing in the launch file,
# but clear them so the run depends on the launch file only
rosparam delete /trajectory_generation_node 2>/dev/null || true

tmux new-session -d -s follow "source ~/lab3_work/env.sh && stdbuf -oL roslaunch trajectory_generation traj_following.launch > $O/traj_following.log 2>&1"
sleep 3
tmux new-session -d -s bag4 "source ~/lab3_work/env.sh && rosbag record -q -O $O/race.bag --duration=16 /current_state /desired_state /desired_traj_vertices /rotor_speed_cmds /tesse/collision /tf"
sleep 1
# Unity view while racing (frames piped to ffmpeg; x11grab is black under WSLg)
( end=$((SECONDS+11)); while [ $SECONDS -lt $end ]; do import -window $SIM ppm:-; done ) | \
  ffmpeg -nostdin -y -loglevel error -f image2pipe -c:v ppm -use_wallclock_as_timestamps 1 -i - \
         -vf "format=yuv420p" -r 15 -c:v libx264 -crf 23 $O/unity_view.mp4 &
CAP=$!
tmux new-session -d -s verts "source ~/lab3_work/env.sh && roslaunch planner_pkg traj_gen.launch > $O/traj_gen.log 2>&1"
wait $CAP
sleep 6
# communication evidence while all nodes are still up; drop registrations
# left by killed 'rostopic echo' helpers first
echo y | rosnode cleanup > /dev/null 2>&1
{
  echo "### rosnode list"; rosnode list
  for n in /trajectory_generation_node /controller_node /traj_vertices_publisher; do
    echo; echo "### rosnode info $n"; rosnode info $n 2>&1 | sed -n '/Publications/,/Services/p'
  done
  echo; for t in /desired_traj_vertices /desired_state /current_state /rotor_speed_cmds; do echo "### rostopic info $t"; rostopic info $t; done
  echo; for t in /desired_traj_vertices /desired_state /current_state /rotor_speed_cmds; do echo "### rostopic hz $t"; timeout 5 rostopic hz $t 2>&1 | tail -2; done
  echo; echo "### parameters"; for k in kx kv kr komega use_omega_d; do echo "$k: $(rosparam get /$k)"; done
  rosparam get /trajectory_generation_node
} > $O/ros_communication.txt 2>&1
python3 $W/rosgraph_dot.py $O/rosgraph.dot && dot -Tpng -Gdpi=150 $O/rosgraph.dot -o $O/rqt_graph.png
sleep 2
python3 $W/race_check.py $O/race.bag --plot $O/race.png --title "official launch files: $1" | tee $O/race_summary.txt
for s in verts follow bag4; do tmux kill-session -t $s 2>/dev/null; done
