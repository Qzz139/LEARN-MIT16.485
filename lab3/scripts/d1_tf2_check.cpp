// Deliverable 1 check: every answer is the one-liner used in the report.
// Build (ROS Noetic):
//   g++ -std=c++14 d1_tf2_check.cpp -I/opt/ros/noetic/include -I/usr/include/eigen3 \
//       -L/opt/ros/noetic/lib -ltf2 -lrostime -lcpp_common -o d1_tf2_check
#include <cstdio>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2/utils.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#include <tf2_eigen/tf2_eigen.h>
#include <Eigen/Geometry>

int main() {
  // Ground truth: roll 0.1, pitch -0.2, yaw 0.7 rad
  tf2::Quaternion truth;
  truth.setRPY(0.1, -0.2, 0.7);
  geometry_msgs::Quaternion quat_msg_in;
  quat_msg_in.x = truth.x(); quat_msg_in.y = truth.y();
  quat_msg_in.z = truth.z(); quat_msg_in.w = truth.w();

  // A.1  geometry_msgs::Quaternion -> tf2::Quaternion
  tf2::Quaternion quat_tf;
  tf2::fromMsg(quat_msg_in, quat_tf);
  printf("A.1 fromMsg: (%.6f, %.6f, %.6f, %.6f)\n", quat_tf.x(), quat_tf.y(), quat_tf.z(), quat_tf.w());

  // A.2  tf2::Quaternion -> geometry_msgs::Quaternion
  geometry_msgs::Quaternion quat_msg = tf2::toMsg(quat_tf);
  printf("A.2 toMsg:   (%.6f, %.6f, %.6f, %.6f)\n", quat_msg.x, quat_msg.y, quat_msg.z, quat_msg.w);

  // A.3  scalar part of a tf2::Quaternion
  printf("A.3 getW():  %.6f\n", quat_tf.getW());

  // B.1  yaw with one call
  tf2::Quaternion quat_t = quat_tf;
  printf("B.1 getYaw:  %.6f (expected 0.700000)\n", tf2::getYaw(quat_t));

  // B.2  geometry_msgs::Quaternion -> Eigen 3x3 matrix (two calls)
  Eigen::Quaterniond quat_eigen;
  tf2::fromMsg(quat_msg, quat_eigen);
  Eigen::Matrix3d R = quat_eigen.toRotationMatrix();

  // Reference matrix built from the same quaternion with tf2 itself
  tf2::Matrix3x3 R_ref(truth);
  double max_err = 0.0;
  for (int i = 0; i < 3; ++i)
    for (int j = 0; j < 3; ++j)
      max_err = std::max(max_err, std::abs(R(i, j) - R_ref[i][j]));
  printf("B.2 toRotationMatrix:\n");
  for (int i = 0; i < 3; ++i) printf("    [% .6f % .6f % .6f]\n", R(i, 0), R(i, 1), R(i, 2));
  printf("    max |R - R_tf2| = %.3e\n", max_err);
  return 0;
}
