import sys
p = sys.argv[1]
s = open(p).read()
old = "        assert(self.prev_time < metadata['time'])\n"
new = ("        if metadata['time'] <= self.prev_time:\n"
       "            # lab4 simulator restarts its clock on the start-up scene change\n"
       "            # (and on respawn): resync instead of killing this thread\n"
       "            rospy.logwarn(\"TESSE_ROS_NODE: sim time went back %.3f -> %.3f, resync\",\n"
       "                          self.prev_time, metadata['time'])\n"
       "            self.prev_time = metadata['time']\n"
       "            return\n")
if old in s:
    open(p, "w").write(s.replace(old, new)); print("patched")
else:
    print("pattern not found (already patched?)")
