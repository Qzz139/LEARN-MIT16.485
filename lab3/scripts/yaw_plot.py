#!/usr/bin/env python3
"""Yaw of the av-desired TF frame vs the drone (base_link_gt): python3 yaw_plot.py run.bag out.png"""
import math
import sys

import numpy as np
import rosbag


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def main(path, out):
    series = {"av-desired": ([], []), "base_link_gt": ([], [])}
    with rosbag.Bag(path) as bag:
        for _, msg, _ in bag.read_messages(topics=["/tf"]):
            for tr in msg.transforms:
                if tr.child_frame_id in series:
                    series[tr.child_frame_id][0].append(tr.header.stamp.to_sec())
                    series[tr.child_frame_id][1].append(yaw_of(tr.transform.rotation))
    t0 = min(s[0][0] for s in series.values())
    data = {k: (np.array(t) - t0, np.unwrap(np.array(y))) for k, (t, y) in series.items()}

    td, yd = data["av-desired"]
    tb, yb = data["base_link_gt"]
    rate = np.polyfit(td, yd, 1)[0]
    yd_at_b = np.interp(tb, td, yd)
    lag = yb - yd_at_b
    lag -= 2 * np.pi * np.round(np.mean(lag) / (2 * np.pi))  # same branch
    print(f"av-desired: {len(td)} samples, yaw rate {rate:.4f} rad/s, total rotation {np.degrees(yd[-1] - yd[0]):.1f} deg in {td[-1]:.1f} s")
    print(f"base_link_gt - av-desired yaw: mean {np.degrees(lag.mean()):.2f} deg, std {np.degrees(lag.std()):.2f} deg")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
    ax[0].plot(td, np.degrees(np.arctan2(np.sin(yd), np.cos(yd))), color="0.4", label="av-desired (desired)")
    ax[0].plot(tb, np.degrees(np.arctan2(np.sin(yb), np.cos(yb))), "--", color="C0", label="base_link_gt (drone)")
    ax[0].set_ylabel("yaw [deg]")
    ax[0].legend(loc="upper right")
    ax[1].plot(tb, np.degrees(lag), color="C1")
    ax[1].set_ylabel("yaw difference [deg]")
    ax[1].set_xlabel("time [s]")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"plot: {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
