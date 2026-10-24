#!/usr/bin/env python3
"""Race summary from a rosbag: python3 race_check.py run.bag [--pass-radius R] [--plot out.png]

Needs /current_state, /desired_state, /desired_traj_vertices (gates) and, if the bridge
was started with publish_collisions:=true, /tesse/collision.
  - gate i is passed when the drone comes within R of the gate centre, in gate order
  - gate time = first entry into the R-ball, interpolated between the 20 ms odometry samples
    (the closest approach can be much later, when the drone hovers at the final gate)
  - race time = from the first /desired_state (trajectory start) to the last gate's time
  - smoothness: share of reversed rotor commands, rotor-command step RMS
"""
import argparse
import math

import numpy as np
import rosbag


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bag")
    ap.add_argument("--pass-radius", type=float, default=0.6)
    ap.add_argument("--plot")
    ap.add_argument("--title", default="")
    args = ap.parse_args()

    gates, gate_yaw = None, None
    t, pos, vel = [], [], []
    des_t, des = [], []
    rot_t, rot = [], []
    coll = []
    with rosbag.Bag(args.bag) as bag:
        for topic, m, tb in bag.read_messages():
            if topic == "/desired_traj_vertices" and gates is None:
                gates = np.array([[p.position.x, p.position.y, p.position.z] for p in m.poses])
                gate_yaw = np.array([yaw_of(p.orientation) for p in m.poses])
            elif topic == "/current_state":
                t.append(m.header.stamp.to_sec())
                p, v = m.pose.pose.position, m.twist.twist.linear
                pos.append([p.x, p.y, p.z])
                vel.append([v.x, v.y, v.z])
            elif topic == "/desired_state":
                p = m.transforms[0].translation
                des_t.append(tb.to_sec())
                des.append([p.x, p.y, p.z])
            elif topic == "/rotor_speed_cmds":
                rot_t.append(tb.to_sec())
                rot.append(list(m.angular_velocities))
            elif topic == "/tesse/collision" and m.is_collision:
                coll.append((m.header.stamp.to_sec(), m.object_name))
    if gates is None:
        raise SystemExit("no /desired_traj_vertices in bag")
    t, pos, vel, des_t, des = map(np.array, (t, pos, vel, des_t, des))
    t0 = des_t[0]                                   # trajectory starts with the first set-point
    k = t >= t0
    t, pos, vel = t[k] - t0, pos[k], vel[k]

    print(f"bag: {args.bag}")
    print(f"gates: {len(gates)}, pass radius {args.pass_radius} m")
    print(" gate |  closest [m]  entry t [s] | speed [m/s] | passed")
    last_t, passed = -1.0, 0
    t_gate = []
    for i, g in enumerate(gates):
        d = np.linalg.norm(pos - g, axis=1)
        # only search after the previous gate so revisits do not count
        ok = t > last_t
        j = np.argmin(np.where(ok, d, np.inf))
        hit = d[j] <= args.pass_radius
        if hit:  # time of the first entry into the pass radius
            j_in = np.nonzero(ok & (d <= args.pass_radius))[0][0]
        else:
            j_in = j
        passed += int(hit and passed == i)
        last_t = t_in = t[j_in]
        if hit and j_in > 0 and d[j_in - 1] > args.pass_radius:  # interpolate the crossing between the 20 ms samples
            t_in = t[j_in - 1] + (d[j_in - 1] - args.pass_radius) / (d[j_in - 1] - d[j_in]) * (t[j_in] - t[j_in - 1])
        t_gate.append(t_in)
        print(f" {i:4d} | {d[j]:11.3f}  {t_in:8.3f} | {np.linalg.norm(vel[j_in]):10.2f}  | {'yes' if hit else 'NO'}")
    finished = passed == len(gates)
    race_time = t_gate[-1] if finished else t[-1]
    print(f"gates passed in order: {passed}/{len(gates)}")
    print(f"race time (trajectory start -> last gate): "
          + (f"{race_time:.3f} s" if finished else f"DNF (stopped at gate {passed}, {t[-1]:.1f} s recorded)"))
    print(f"max speed: {np.max(np.linalg.norm(vel, axis=1)):.2f} m/s")
    # resting on the floor before take-off reports Floor contacts: only count airborne ones
    airborne = np.nonzero(pos[:, 2] > 0.5)[0]
    t_air = t[airborne[0]] if len(airborne) else np.inf
    in_race = [(tc - t0, name) for tc, name in coll if t0 + t_air <= tc <= t0 + race_time + 1.0]
    names = sorted({n for _, n in in_race})
    print(f"take-off (z > 0.5 m) at {t_air:.2f} s; airborne collisions during the race: {len(in_race)}"
          + ("" if not in_race else "  objects: " + ", ".join(names)
             + "  first at " + f"{in_race[0][0]:.2f}s"))
    if rot:
        rot_t, rot = np.array(rot_t), np.array(rot)
        kr = (rot_t >= t0) & (rot_t <= t0 + race_time)
        r = rot[kr]
        print(f"rotor commands: mean {r.mean():.1f} rad/s, reversed {np.mean(r < 0) * 100:.1f} %, "
              f"step rms {np.sqrt(np.mean(np.diff(r, axis=0) ** 2)):.1f} rad/s")

    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.3, 1]})
        kd = des_t >= t0
        ax[0].plot(des[kd, 0], des[kd, 1], "--", color="0.5", label="desired")
        ax[0].plot(pos[:, 0], pos[:, 1], color="C0", label="actual")
        for i, (g, yw) in enumerate(zip(gates, gate_yaw)):
            ax[0].plot(g[0], g[1], "s", color="C3", ms=6)
            ax[0].arrow(g[0], g[1], 1.5 * math.cos(yw), 1.5 * math.sin(yw), color="C3", width=0.05)
            ax[0].annotate(str(i), (g[0], g[1]), textcoords="offset points", xytext=(6, 6))
        ax[0].set_aspect("equal")
        ax[0].set_xlabel("x [m]")
        ax[0].set_ylabel("y [m]")
        ax[0].legend()
        ax[0].set_title("top view (red: gates, arrow = gate yaw)")
        ax[1].plot(t, pos[:, 2], color="C0", label="actual z")
        ax[1].plot(des_t[kd] - t0, des[kd, 2], "--", color="0.5", label="desired z")
        for i, tg in enumerate(t_gate):
            ax[1].axvline(tg, color="C3", alpha=0.3)
        ax[1].set_xlabel("time since trajectory start [s]")
        ax[1].set_ylabel("z [m]")
        ax[1].legend()
        ax[1].set_title((f"race time {race_time:.3f} s" if finished else "DNF") + f", {passed}/{len(gates)} gates")
        fig.suptitle(args.title)
        fig.tight_layout()
        fig.savefig(args.plot, dpi=140)
        print(f"plot: {args.plot}")


if __name__ == "__main__":
    main()
