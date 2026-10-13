#!/usr/bin/env python3
"""Smoothness of a circle run: python3 jitter_check.py run.bag [--skip SEC]

On the steady circle the bank angle is constant, so roll/pitch rates should stay near
zero and the rotor speeds near constant. Reported per run:
  - roll/pitch jitter: RMS of roll/pitch minus a 0.5 s moving average [deg]
  - body roll/pitch rate RMS [deg/s]
  - rotor command step: RMS change between consecutive commands [rad/s]
  - position error RMS [m]
"""
import argparse
import math

import numpy as np
import rosbag


def rpy(q):
    x, y, z, w = q
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x))))
    return roll, pitch


def quat_to_R(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bag")
    ap.add_argument("--skip", type=float, default=8.0)
    args = ap.parse_args()

    t, att, wb, pos = [], [], [], []
    des_t, des = [], []
    rt, rs = [], []
    with rosbag.Bag(args.bag) as bag:
        for topic, m, tb in bag.read_messages(topics=["/current_state", "/desired_state", "/rotor_speed_cmds"]):
            if topic == "/current_state":
                o = m.pose.pose.orientation
                q = (o.x, o.y, o.z, o.w)
                a = m.twist.twist.angular
                t.append(tb.to_sec())
                att.append(rpy(q))
                wb.append(quat_to_R(q).T @ np.array([a.x, a.y, a.z]))
                p = m.pose.pose.position
                pos.append([p.x, p.y, p.z])
            elif topic == "/desired_state":
                p = m.transforms[0].translation
                des_t.append(tb.to_sec())
                des.append([p.x, p.y, p.z])
            else:
                rt.append(tb.to_sec())
                rs.append(list(m.angular_velocities))
    t, att, wb, pos = map(np.array, (t, att, wb, pos))
    des_t, des, rt, rs = map(np.array, (des_t, des, rt, rs))
    t0 = t[0]
    k = (t - t0) >= args.skip
    kr = (rt - t0) >= args.skip

    dt = np.mean(np.diff(t))
    n = max(1, int(round(0.5 / dt)))
    kernel = np.ones(n) / n
    jit = []
    for i in range(2):
        a = np.unwrap(att[:, i])
        smooth = np.convolve(a, kernel, mode="same")
        jit.append(np.degrees(np.sqrt(np.mean((a - smooth)[k][n:-n] ** 2))))
    rate_rms = np.degrees(np.sqrt(np.mean(wb[k][:, :2] ** 2, axis=0)))
    step = np.sqrt(np.mean(np.diff(rs[kr], axis=0) ** 2))
    idx = np.searchsorted(des_t, t, side="right") - 1
    ok = k & (idx >= 0)
    e = np.linalg.norm(pos[ok] - des[idx[ok]], axis=1)

    print(f"{args.bag.split('/')[-1]}: roll/pitch jitter {jit[0]:.2f}/{jit[1]:.2f} deg, "
          f"roll/pitch rate rms {rate_rms[0]:.1f}/{rate_rms[1]:.1f} deg/s, "
          f"rotor step rms {step:.1f} rad/s, rotor mean {rs[kr].mean():.1f} rad/s, "
          f"pos err rms {np.sqrt(np.mean(e ** 2)):.3f} m")


if __name__ == "__main__":
    main()
