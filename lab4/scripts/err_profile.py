"""Tracking error vs desired acceleration around the first gates of a race."""
import sys, numpy as np, rosbag
for path in sys.argv[1:]:
    dt_, des, dacc, ct, cur = [], [], [], [], []
    gates = None
    with rosbag.Bag(path) as bag:
        for topic, m, tb in bag.read_messages(topics=["/desired_state", "/current_state", "/desired_traj_vertices"]):
            if topic == "/desired_state":
                p, a = m.transforms[0].translation, m.accelerations[0].linear
                dt_.append(tb.to_sec()); des.append([p.x, p.y, p.z]); dacc.append([a.x, a.y, a.z])
            elif topic == "/current_state":
                p = m.pose.pose.position; ct.append(tb.to_sec()); cur.append([p.x, p.y, p.z])
            elif gates is None:
                gates = np.array([[q.position.x, q.position.y, q.position.z] for q in m.poses])
    dt_, des, dacc, ct, cur = map(np.array, (dt_, des, dacc, ct, cur))
    t0 = dt_[0]
    idx = np.searchsorted(dt_, ct, side="right") - 1
    ok = idx >= 0
    tt, err = ct[ok] - t0, np.linalg.norm(cur[ok] - des[idx[ok]], axis=1)
    acc = np.linalg.norm(dacc[idx[ok]], axis=1)
    print(path.split("/")[-1])
    for lo, hi in [(0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.0), (3.0, 3.5)]:
        k = (tt >= lo) & (tt < hi)
        print(f"  t {lo:.1f}-{hi:.1f}s: track err mean {err[k].mean():.2f} max {err[k].max():.2f} m | desired |acc| max {acc[k].max():5.1f} | z_cur {cur[ok][k][:,2].mean():.2f}")
    for g in (0, 1, 2):
        d = np.linalg.norm(cur - gates[g], axis=1); j = np.argmin(d)
        print(f"  gate {g}: closest {d[j]:.2f} m at t={ct[j]-t0:.2f}s, offset (x,y,z) {np.round(cur[j]-gates[g], 2)}")
