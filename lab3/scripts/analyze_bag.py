#!/usr/bin/env python3
"""Tracking-error summary for one run: python3 analyze_bag.py run.bag [--skip SEC] [--plot out.png]

/desired_state has no header. If the bag contains /tf, the desired pose is taken from the
stamped av-desired transform and interpolated at the odometry header stamps (exact sim-time
alignment). Otherwise each /current_state sample is paired with the latest /desired_state
received before it, which can be off by one 20 ms sample (fuzz of ~v*20 ms in the error).
"""
import argparse
import math

import numpy as np
import rosbag


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def load(path):
    des_t, des = [], []
    cur_t, cur = [], []
    tf_t, tf_des = [], []
    cur_stamp = []
    with rosbag.Bag(path) as bag:
        for topic, msg, t in bag.read_messages(topics=["/desired_state", "/current_state", "/tf"]):
            if topic == "/desired_state":
                p, q = msg.transforms[0].translation, msg.transforms[0].rotation
                des_t.append(t.to_sec())
                des.append([p.x, p.y, p.z, yaw_of(q)])
            elif topic == "/current_state":
                p, q = msg.pose.pose.position, msg.pose.pose.orientation
                cur_t.append(t.to_sec())
                cur_stamp.append(msg.header.stamp.to_sec())
                cur.append([p.x, p.y, p.z, yaw_of(q)])
            else:
                for tr in msg.transforms:
                    if tr.child_frame_id == "av-desired":
                        p, q = tr.transform.translation, tr.transform.rotation
                        tf_t.append(tr.header.stamp.to_sec())
                        tf_des.append([p.x, p.y, p.z, yaw_of(q)])
    return (np.array(des_t), np.array(des), np.array(cur_t), np.array(cur),
            np.array(tf_t), np.array(tf_des), np.array(cur_stamp))


def desired_at(tf_t, tf_des, t):
    """Interpolate the stamped av-desired pose (yaw unwrapped) at times t."""
    order = np.argsort(tf_t, kind="stable")
    tt, dd = tf_t[order], tf_des[order]
    tt, keep = np.unique(tt, return_index=True)
    dd = dd[keep]
    yaw = np.unwrap(dd[:, 3])
    return np.column_stack([np.interp(t, tt, dd[:, i]) for i in range(3)] + [np.interp(t, tt, yaw)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bag")
    ap.add_argument("--skip", type=float, default=0.0, help="ignore the first SEC seconds (take-off transient)")
    ap.add_argument("--plot", help="save a figure with xy path and error vs time")
    ap.add_argument("--title", default="")
    args = ap.parse_args()

    des_t, des, cur_t, cur, tf_t, tf_des, cur_stamp = load(args.bag)
    if len(tf_t) > 1:
        ok = (cur_stamp >= tf_t.min()) & (cur_stamp <= tf_t.max())
        cur_t, cur = cur_stamp[ok], cur[ok]
        des_m = desired_at(tf_t, tf_des, cur_t)
        print("alignment: av-desired TF interpolated at odometry header stamps")
    else:
        idx = np.searchsorted(des_t, cur_t, side="right") - 1
        ok = idx >= 0
        cur_t, cur, des_m = cur_t[ok], cur[ok], des[idx[ok]]
        print("alignment: latest /desired_state by bag receive time")
    t = cur_t - cur_t[0]
    keep = t >= args.skip

    e_pos = np.linalg.norm(cur[:, :3] - des_m[:, :3], axis=1)
    e_yaw = np.degrees(np.abs(np.arctan2(np.sin(cur[:, 3] - des_m[:, 3]), np.cos(cur[:, 3] - des_m[:, 3]))))
    k = keep
    print(f"bag: {args.bag}")
    print(f"samples: {k.sum()} over {t[k][-1] - t[k][0]:.1f} s (skip first {args.skip:.1f} s)")
    print(f"position error [m]: rms {np.sqrt(np.mean(e_pos[k] ** 2)):.3f}, mean {e_pos[k].mean():.3f}, max {e_pos[k].max():.3f}")
    print(f"yaw error [deg]:    rms {np.sqrt(np.mean(e_yaw[k] ** 2)):.2f}, max {e_yaw[k].max():.2f}")
    print(f"altitude: mean {cur[k, 2].mean():.3f} m (desired mean {des_m[k, 2].mean():.3f} m)")

    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 2, figsize=(10, 4))
        ax[0].plot(des_m[:, 0], des_m[:, 1], "--", color="0.5", label="desired")
        ax[0].plot(cur[:, 0], cur[:, 1], color="C0", label="actual")
        ax[0].set_aspect("equal")
        ax[0].set_xlabel("x [m]")
        ax[0].set_ylabel("y [m]")
        ax[0].legend()
        ax[0].set_title("xy path")
        ax[1].plot(t, e_pos, color="C0", label="position error [m]")
        ax[1].set_xlabel("time [s]")
        ax[1].set_ylabel("position error [m]")
        ax2 = ax[1].twinx()
        ax2.plot(t, e_yaw, color="C1", alpha=0.7, label="yaw error [deg]")
        ax2.set_ylabel("yaw error [deg]")
        ax[1].set_title("tracking error")
        fig.suptitle(args.title)
        fig.tight_layout()
        fig.savefig(args.plot, dpi=150)
        print(f"plot: {args.plot}")


if __name__ == "__main__":
    main()
