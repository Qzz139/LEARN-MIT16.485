//
// Created by stewart on 9/20/20.
//

#include <eigen_conversions/eigen_msg.h>
#include <geometry_msgs/PoseArray.h>
#include <nav_msgs/Odometry.h>
#include <ros/ros.h>
#include <trajectory_msgs/MultiDOFJointTrajectory.h>

#include <mav_trajectory_generation/polynomial_optimization_linear.h>
#include <mav_trajectory_generation/polynomial_optimization_nonlinear.h>
#include <mav_trajectory_generation/trajectory.h>

#include <tf/transform_datatypes.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#include <eigen3/Eigen/Dense>

class WaypointFollower {
  [[maybe_unused]] ros::Subscriber currentStateSub;
  [[maybe_unused]] ros::Subscriber poseArraySub;
  ros::Publisher desiredStatePub;

  // Current state
  Eigen::Vector3d x;  // current position of the UAV's c.o.m. in the world frame
  bool got_current_state = false;  // x is only valid after the first odometry
  double current_yaw = 0;          // start the yaw trajectory where the drone points

  ros::Timer desiredStateTimer;

  ros::Time trajectoryStartTime;
  mav_trajectory_generation::Trajectory trajectory;
  mav_trajectory_generation::Trajectory yaw_trajectory;

  void onCurrentState(nav_msgs::Odometry const& cur_state) {
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    //  PART 1.1 |  16.485 - Fall 2021  - Lab 4 coding assignment (5 pts)
    // ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~  ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    // ~
    //
    //  Populate the variable x, which encodes the current world position of the
    //  UAV
    // ~~~~ begin solution
    const geometry_msgs::Point& p = cur_state.pose.pose.position;
    x << p.x, p.y, p.z;
    current_yaw = tf::getYaw(cur_state.pose.pose.orientation);
    got_current_state = true;
    // ~~~~ end solution
    // ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    // ~
    //                                 end part 1.1
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  }

  void generateOptimizedTrajectory(geometry_msgs::PoseArray const& poseArray) {
    if (poseArray.poses.size() < 1) {
      ROS_ERROR("Must have at least one pose to generate trajectory!");
      trajectory.clear();
      yaw_trajectory.clear();
      return;
    }

    if (!trajectory.empty()) return;

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    //  PART 1.2 |  16.485 - Fall 2021  - Lab 4 coding assignment (35 pts)
    // ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~  ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    // ~
    //
    //  We are using the mav_trajectory_generation library
    //  (https://github.com/ethz-asl/mav_trajectory_generation) to perform
    //  trajectory optimization given the waypoints (based on the position and
    //  orientation of the gates on the race course).
    //  We will be finding the trajectory for the position and the trajectory
    //  for the yaw in a decoupled manner.
    //  In this section:
    //  1. Fill in the correct number for D, the dimension we should apply to
    //  the solver to find the positional trajectory
    //  2. Correctly populate the Vertex::Vector structure below (vertices,
    //  yaw_vertices) using the position of the waypoints and the yaw of the
    //  waypoints respectively
    //
    //  Hints:
    //  1. Use vertex.addConstraint(POSITION, position) where position is of
    //  type Eigen::Vector3d to enforce a waypoint position.
    //  2. Use vertex.addConstraint(ORIENTATION, yaw) where yaw is a double
    //  to enforce a waypoint yaw.
    //  3. Remember angle wraps around 2 pi. Be careful!
    //  4. For the ending waypoint for position use .makeStartOrEnd as seen with
    //  the starting waypoint instead of .addConstraint as you would do for the
    //  other waypoints.
    //
    // ~~~~ begin solution
    // The start vertex is the current position: wait for the first odometry
    // (the gates are re-published at 5 Hz, so we simply try again later).
    if (!got_current_state) {
      ROS_WARN_THROTTLE(1.0, "No odometry yet, postponing trajectory generation");
      return;
    }

    const int D = 3;  // dimension of each vertex in the trajectory
    mav_trajectory_generation::Vertex start_position(D), end_position(D);
    mav_trajectory_generation::Vertex::Vector vertices;
    mav_trajectory_generation::Vertex start_yaw(1), end_yaw(1);
    mav_trajectory_generation::Vertex::Vector yaw_vertices;

    // ============================================
    // Convert the pose array to a list of vertices
    // ============================================

    // Start from the current position and orientation (the drone spawns at
    // about -166 deg; starting the yaw at 0 would spin it round first)
    using namespace mav_trajectory_generation::derivative_order;
    start_position.makeStartOrEnd(x, SNAP);
    vertices.push_back(start_position);
    start_yaw.addConstraint(ORIENTATION, current_yaw);
    yaw_vertices.push_back(start_yaw);

    // ~exit_distance > 0: end the trajectory that far beyond the last gate, so
    // the last gate is flown through at speed instead of being a full stop.
    double exit_distance;
    ros::param::param("~exit_distance", exit_distance, 0.0);

    double last_yaw = current_yaw;
    for (auto i = 0; i < poseArray.poses.size(); ++i) {
      const geometry_msgs::Pose& gate = poseArray.poses[i];
      const bool is_last = (i + 1 == poseArray.poses.size()) && exit_distance <= 0;

      // Populate vertices (for the waypoint positions)
      Eigen::Vector3d position(gate.position.x, gate.position.y, gate.position.z);
      if (is_last) {
        end_position.makeStartOrEnd(position, SNAP);
        vertices.push_back(end_position);
      } else {
        mav_trajectory_generation::Vertex vertex(D);
        vertex.addConstraint(POSITION, position);
        vertices.push_back(vertex);
      }

      // Populate yaw_vertices (for the waypoint yaw angles)
      // Unwrap so that consecutive yaw waypoints differ by less than pi,
      // otherwise the optimizer spins the drone the long way round.
      double yaw = tf::getYaw(gate.orientation);
      while (yaw - last_yaw > M_PI) yaw -= 2 * M_PI;
      while (yaw - last_yaw < -M_PI) yaw += 2 * M_PI;
      last_yaw = yaw;
      if (is_last) {
        end_yaw.addConstraint(ORIENTATION, yaw);
        yaw_vertices.push_back(end_yaw);
      } else {
        mav_trajectory_generation::Vertex yaw_vertex(1);
        yaw_vertex.addConstraint(ORIENTATION, yaw);
        yaw_vertices.push_back(yaw_vertex);
      }
    }

    if (exit_distance > 0) {
      // stop point straight ahead of the last gate (gate yaw = flight direction)
      const geometry_msgs::Pose& gate = poseArray.poses.back();
      const double gate_yaw = tf::getYaw(gate.orientation);
      Eigen::Vector3d exit_point(gate.position.x + exit_distance * cos(gate_yaw),
                                 gate.position.y + exit_distance * sin(gate_yaw),
                                 gate.position.z);
      end_position.makeStartOrEnd(exit_point, SNAP);
      vertices.push_back(end_position);
      end_yaw.addConstraint(ORIENTATION, last_yaw);
      yaw_vertices.push_back(end_yaw);
    }

    // ~~~~ end solution
    // ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    // ~
    //                                 end part 1.2
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    // ============================================================
    // Estimate the time to complete each segment of the trajectory
    // ============================================================

    // HINT: play with these segment times and see if you can finish
    // the race course faster!
    std::vector<double> segment_times;
    // limits used for the time allocation; ROS params so races can be tuned
    // without recompiling (template defaults: 8 m/s, 4 m/s^2)
    double v_max, a_max;
    ros::param::param("~v_max", v_max, 8.0);
    ros::param::param("~a_max", a_max, 4.0);
    // ~time_mode 0: library heuristic (template). Its large constant gives short
    // segments relatively more time, and the uneven distance/time ratios make
    // the min-snap solution ring (z swung 0.9-4.3 m between gates at 2-3.6 m).
    // ~time_mode 1: time proportional to distance at a cruise speed of v_max.
    // The first and last segments start/end at rest, so their average speed is
    // only about v/2: give them 2d/v, otherwise the deficit rings through the
    // whole trajectory (peak speed 2.4x cruise, z up to 4.7 m in a 5 m room).
    // ~start_factor scales the take-off segment (the first one leaves the floor).
    int time_mode;
    double start_factor;
    ros::param::param("~time_mode", time_mode, 0);
    ros::param::param("~start_factor", start_factor, 2.0);
    if (time_mode == 1) {
      for (size_t i = 0; i + 1 < vertices.size(); ++i) {
        Eigen::VectorXd p0, p1;
        vertices[i].getConstraint(POSITION, &p0);
        vertices[i + 1].getConstraint(POSITION, &p1);
        double factor = 1.0;
        if (i == 0) factor = start_factor;
        else if (i + 2 == vertices.size()) factor = 2.0;
        segment_times.push_back(std::max((p1 - p0).norm() / v_max * factor, 0.2));
      }
    } else {
      segment_times = estimateSegmentTimes(vertices, v_max, a_max);
    }
    // ~segment_scale: optional per-segment multipliers (segment i joins vertex i
    // and i+1; vertex 0 is the start, vertex k the gate k-1). Used to slow down
    // only the turns the controller cannot follow at full speed.
    std::vector<double> segment_scale;
    if (ros::param::get("~segment_scale", segment_scale)) {
      for (size_t i = 0; i < segment_times.size() && i < segment_scale.size(); ++i)
        segment_times[i] *= segment_scale[i];
    }
    ROS_INFO("Segment times (mode %d) from v_max = %.2f m/s, a_max = %.2f m/s^2",
             time_mode, v_max, a_max);

    // =====================================================
    // Solve for the optimized trajectory
    // =====================================================
    // Position. Default: linear solve with the segment times above (as in the
    // handout). With ~nonlinear the library also optimises the segment times
    // under velocity/acceleration magnitude limits (Richter et al.), which
    // removes the ringing that short heuristic segment times cause.
    const int N = 10;
    bool nonlinear;
    ros::param::param("~nonlinear", nonlinear, false);
    if (nonlinear) {
      mav_trajectory_generation::NonlinearOptimizationParameters parameters;
      parameters.max_iterations = 1000;
      parameters.f_rel = 0.05;
      parameters.x_rel = 0.1;
      ros::param::param("~time_penalty", parameters.time_penalty, 500.0);
      parameters.initial_stepsize_rel = 0.1;
      parameters.inequality_constraint_tolerance = 0.1;
      int time_alloc = parameters.time_alloc_method;
      ros::param::param("~time_alloc_method", time_alloc, time_alloc);
      parameters.time_alloc_method = static_cast<
          mav_trajectory_generation::NonlinearOptimizationParameters::TimeAllocMethod>(time_alloc);
      ros::param::param("~print_debug", parameters.print_debug_info, false);
      parameters.print_debug_info_time_allocation = parameters.print_debug_info;
      mav_trajectory_generation::PolynomialOptimizationNonLinear<N> opt(D, parameters);
      opt.setupFromVertices(vertices, segment_times, SNAP);
      opt.addMaximumMagnitudeConstraint(VELOCITY, v_max);
      opt.addMaximumMagnitudeConstraint(ACCELERATION, a_max);
      const int result = opt.optimize();
      ROS_INFO("nlopt result %d (time allocation method %d, time penalty %.0f)",
               result, time_alloc, parameters.time_penalty);
      opt.getTrajectory(&trajectory);
      segment_times = trajectory.getSegmentTimes();
    } else {
      mav_trajectory_generation::PolynomialOptimization<N> opt(D);
      opt.setupFromVertices(vertices, segment_times, SNAP);
      opt.solveLinear();
      opt.getTrajectory(&trajectory);
    }

    // Yaw, on the same segment times as the position trajectory
    mav_trajectory_generation::PolynomialOptimization<N> yaw_opt(1);
    yaw_opt.setupFromVertices(yaw_vertices, segment_times, SNAP);
    yaw_opt.solveLinear();
    yaw_opt.getTrajectory(&yaw_trajectory);
    trajectoryStartTime = ros::Time::now();

    ROS_INFO("Generated %s trajectory from %zu waypoints, duration %.2f s",
             nonlinear ? "time-optimised" : "linear", vertices.size(),
             trajectory.getMaxTime());

    // Peak speed/acceleration and altitude range of the plan (sanity check)
    double peak_v = 0, peak_a = 0, z_min = 1e9, z_max = -1e9;
    for (double ts = 0; ts <= trajectory.getMaxTime(); ts += 0.02) {
      peak_v = std::max(peak_v, trajectory.evaluate(ts, VELOCITY).norm());
      peak_a = std::max(peak_a, trajectory.evaluate(ts, ACCELERATION).norm());
      const double z = trajectory.evaluate(ts, POSITION).z();
      z_min = std::min(z_min, z);
      z_max = std::max(z_max, z);
    }
    ROS_INFO("Plan: peak speed %.2f m/s, peak acceleration %.2f m/s^2, z in [%.2f, %.2f] m",
             peak_v, peak_a, z_min, z_max);
  }

  void publishDesiredState(ros::TimerEvent const& ev) {
    if (trajectory.empty()) return;

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    //  PART 1.3 |  16.485 - Fall 2021  - Lab 4 coding assignment (15 pts)
    // ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~  ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    // ~
    //
    //  Finally we get to send commands to our controller! First fill in
    //  properly the value for 'nex_point.time_from_start' and 'sampling_time'
    //  (hint: not 0) and after extracting the state information from our
    //  optimized trajectory, finish populating next_point.
    //
    // ~~~~ begin solution
    trajectory_msgs::MultiDOFJointTrajectoryPoint next_point;

    // time elapsed since the trajectory was generated; hold the final point
    double sampling_time = (ros::Time::now() - trajectoryStartTime).toSec();
    if (sampling_time > trajectory.getMaxTime())
      sampling_time = trajectory.getMaxTime();
    next_point.time_from_start = ros::Duration(sampling_time);

    // Getting the desired state based on the optimized trajectory we found.
    using namespace mav_trajectory_generation::derivative_order;
    Eigen::Vector3d des_position = trajectory.evaluate(sampling_time, POSITION);
    Eigen::Vector3d des_velocity = trajectory.evaluate(sampling_time, VELOCITY);
    Eigen::Vector3d des_accel =
        trajectory.evaluate(sampling_time, ACCELERATION);
    Eigen::VectorXd des_orientation =
        yaw_trajectory.evaluate(sampling_time, ORIENTATION);
    ROS_INFO_THROTTLE(1.0, "Traversed %f percent of the trajectory.",
                      sampling_time / trajectory.getMaxTime() * 100);

    // Populate next_point
    next_point.transforms.resize(1);
    next_point.transforms[0].translation.x = des_position.x();
    next_point.transforms[0].translation.y = des_position.y();
    next_point.transforms[0].translation.z = des_position.z();
    next_point.transforms[0].rotation =
        tf::createQuaternionMsgFromYaw(des_orientation(0));

    next_point.velocities.resize(1);
    next_point.velocities[0].linear.x = des_velocity.x();
    next_point.velocities[0].linear.y = des_velocity.y();
    next_point.velocities[0].linear.z = des_velocity.z();

    // Angular velocity of the reference from differential flatness (Mellinger &
    // Kumar 2011), in world frame. Only used by the controller when its
    // use_omega_d parameter is set (attitude feed-forward for sharp turns).
    const Eigen::Vector3d des_jerk = trajectory.evaluate(sampling_time, JERK);
    const double yaw_rate =
        yaw_trajectory.evaluate(sampling_time, ANGULAR_VELOCITY)(0);
    const Eigen::Vector3d thrust_dir = des_accel + Eigen::Vector3d(0, 0, 9.81);
    const double thrust_norm = thrust_dir.norm();
    Eigen::Vector3d omega_world = Eigen::Vector3d::Zero();
    if (thrust_norm > 1e-3) {
      const Eigen::Vector3d zb = thrust_dir / thrust_norm;
      const Eigen::Vector3d xc(cos(des_orientation(0)), sin(des_orientation(0)), 0);
      const Eigen::Vector3d yb = zb.cross(xc).normalized();
      const Eigen::Vector3d xb = yb.cross(zb);
      // d(zb)/dt = omega x zb = -p yb + q xb
      const Eigen::Vector3d h = (des_jerk - zb.dot(des_jerk) * zb) / thrust_norm;
      omega_world = -h.dot(yb) * xb + h.dot(xb) * yb + yaw_rate * zb.z() * zb;
    }
    next_point.velocities[0].angular.x = omega_world.x();
    next_point.velocities[0].angular.y = omega_world.y();
    next_point.velocities[0].angular.z = omega_world.z();

    next_point.accelerations.resize(1);
    next_point.accelerations[0].linear.x = des_accel.x();
    next_point.accelerations[0].linear.y = des_accel.y();
    next_point.accelerations[0].linear.z = des_accel.z();

    desiredStatePub.publish(next_point);

    // ~~~~ end solution
    // ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    // ~
    //                                 end part 1.3
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  }

 public:
  explicit WaypointFollower(ros::NodeHandle& nh) {
    currentStateSub = nh.subscribe(
        "/current_state", 1, &WaypointFollower::onCurrentState, this);
    poseArraySub = nh.subscribe("/desired_traj_vertices",
                                1,
                                &WaypointFollower::generateOptimizedTrajectory,
                                this);
    desiredStatePub =
        nh.advertise<trajectory_msgs::MultiDOFJointTrajectoryPoint>(
            "/desired_state", 1);
    // 5 Hz moved the set-point up to 1.6 m per step at racing speed; publish
    // at the odometry rate instead.
    desiredStateTimer = nh.createTimer(
        ros::Rate(50), &WaypointFollower::publishDesiredState, this);
    desiredStateTimer.start();
  }
};

int main(int argc, char** argv) {
  ros::init(argc, argv, "trajectory_generation_node");
  ros::NodeHandle nh;

  WaypointFollower waypointFollower(nh);

  ros::spin();
  return 0;
}
