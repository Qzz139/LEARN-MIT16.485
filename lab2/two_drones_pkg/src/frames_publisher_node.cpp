// Publishes the poses of the two drones on tf at 50 Hz:
//   world -> av1: unit circle in the x-y plane, y axis tangent to the path
//   world -> av2: parabola arc in the x-z plane, no rotation
#include <ros/ros.h>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2/LinearMath/Quaternion.h>
#include <geometry_msgs/TransformStamped.h>

#include <cmath>

class FramesPublisherNode {
  ros::NodeHandle nh;
  ros::Time startup_time;
  ros::Timer heartbeat;
  tf2_ros::TransformBroadcaster broadcaster;

 public:
  FramesPublisherNode() {
    startup_time = ros::Time::now();
    // Call onPublish() every 0.02 s, i.e. at 50 Hz.
    heartbeat = nh.createTimer(ros::Duration(0.02), &FramesPublisherNode::onPublish, this);
  }

  void onPublish(const ros::TimerEvent&) {
    // 1. Elapsed time t in seconds. The clock is read once,
    //    so t and both stamps agree.
    const ros::Time now = ros::Time::now();
    const double time = (now - startup_time).toSec();

    // 2. AV1 at (cos t, sin t, 0). yaw = t turns its y axis
    //    into (-sin t, cos t, 0), the direction of motion;
    //    roll = pitch = 0 keeps z_1 parallel to z_w.
    geometry_msgs::TransformStamped AV1World;
    AV1World.header.stamp = now;
    AV1World.header.frame_id = "world";
    AV1World.child_frame_id = "av1";
    AV1World.transform.translation.x = std::cos(time);
    AV1World.transform.translation.y = std::sin(time);
    AV1World.transform.translation.z = 0.0;
    tf2::Quaternion q_av1;
    q_av1.setRPY(0.0, 0.0, time);
    AV1World.transform.rotation.x = q_av1.x();
    AV1World.transform.rotation.y = q_av1.y();
    AV1World.transform.rotation.z = q_av1.z();
    AV1World.transform.rotation.w = q_av1.w();

    // 3. AV2 at (sin t, 0, cos 2t), identity rotation.
    //    Message fields start at 0, so only w = 1 is set.
    geometry_msgs::TransformStamped AV2World;
    AV2World.header.stamp = now;
    AV2World.header.frame_id = "world";
    AV2World.child_frame_id = "av2";
    AV2World.transform.translation.x = std::sin(time);
    AV2World.transform.translation.y = 0.0;
    AV2World.transform.translation.z = std::cos(2 * time);
    AV2World.transform.rotation.w = 1.0;

    // 4. Publish both transforms on /tf.
    broadcaster.sendTransform(AV1World);
    broadcaster.sendTransform(AV2World);
  }
};

int main(int argc, char** argv) {
  ros::init(argc, argv, "frames_publisher_node");
  FramesPublisherNode node;
  ros::spin();
  return 0;
}
