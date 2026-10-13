#!/usr/bin/env python3
"""Republish /desired_traj_vertices with frame_id 'world' on /gates_world for rviz.

traj_vertices_publisher leaves header.frame_id empty, so rviz cannot place the gates.
"""
import rospy
from geometry_msgs.msg import PoseArray

rospy.init_node("gate_relay")
pub = rospy.Publisher("/gates_world", PoseArray, queue_size=1, latch=True)


def relay(msg):
    msg.header.frame_id = "world"
    pub.publish(msg)


rospy.Subscriber("/desired_traj_vertices", PoseArray, relay)
rospy.spin()
