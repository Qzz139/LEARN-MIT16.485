#!/usr/bin/env python3
"""Which frame are /current_state twist.linear and twist.angular expressed in?

    python3 frame_check.py run.bag

Ground truth comes from the pose itself (header stamps):
  v_world  = central difference of position
  w_body   = vee(log(R_k^T R_{k+1})) / dt,   w_world = R_k w_body
and each twist field is compared against both hypotheses (relative RMS error).
"""
import sys

import numpy as np
import rosbag
from scipy.spatial.transform import Rotation


def main(path):
    t, p, q, v, w = [], [], [], [], []
    with rosbag.Bag(path) as bag:
        for _, m, _ in bag.read_messages(topics=["/current_state"]):
            t.append(m.header.stamp.to_sec())
            pp, qq = m.pose.pose.position, m.pose.pose.orientation
            p.append([pp.x, pp.y, pp.z])
            q.append([qq.x, qq.y, qq.z, qq.w])
            v.append([m.twist.twist.linear.x, m.twist.twist.linear.y, m.twist.twist.linear.z])
            w.append([m.twist.twist.angular.x, m.twist.twist.angular.y, m.twist.twist.angular.z])
    t, p, v, w = map(np.array, (t, p, v, w))
    R = Rotation.from_quat(q)
    Rm = R.as_matrix() if hasattr(R, "as_matrix") else R.as_dcm()  # scipy < 1.4 on Noetic

    # linear velocity, samples 1..N-2
    v_fd = (p[2:] - p[:-2]) / (t[2:] - t[:-2])[:, None]
    v_msg = v[1:-1]
    v_msg_as_body = np.einsum("nij,nj->ni", Rm[1:-1], v_msg)  # if v_msg is body, R v_msg is world

    # angular velocity between consecutive samples, compared at the midpoint
    dR = R[:-1].inv() * R[1:]
    w_body_fd = dR.as_rotvec() / (t[1:] - t[:-1])[:, None]
    w_world_fd = np.einsum("nij,nj->ni", Rm[:-1], w_body_fd)
    w_mid = 0.5 * (w[:-1] + w[1:])

    def rel(a, b):
        return np.sqrt(np.mean(np.sum((a - b) ** 2, axis=1))) / np.sqrt(np.mean(np.sum(b ** 2, axis=1)))

    print(f"bag: {path}, {len(t)} odometry samples, mean dt {np.mean(np.diff(t)) * 1e3:.1f} ms")
    print(f"|v| rms {np.sqrt(np.mean(np.sum(v_fd ** 2, 1))):.3f} m/s, |w| rms {np.sqrt(np.mean(np.sum(w_body_fd ** 2, 1))):.3f} rad/s")
    print("relative RMS error of the twist field under each hypothesis (smaller wins):")
    print(f"  linear : world {rel(v_msg, v_fd):.3f}   body {rel(v_msg_as_body, v_fd):.3f}")
    print(f"  angular: world {rel(w_mid, w_world_fd):.3f}   body {rel(w_mid, w_body_fd):.3f}")


if __name__ == "__main__":
    main(sys.argv[1])
