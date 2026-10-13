"""Commanded vs realised specific thrust during a race (is the simulator capping the rotors?)."""
import sys, numpy as np, rosbag
from scipy.spatial.transform import Rotation
cf = 1e-3
for path in sys.argv[1:]:
    t, v, q, rt, rs = [], [], [], [], []
    with rosbag.Bag(path) as bag:
        for topic, m, tb in bag.read_messages(topics=["/current_state", "/rotor_speed_cmds"]):
            if topic == "/current_state":
                t.append(m.header.stamp.to_sec()); vv = m.twist.twist.linear; v.append([vv.x, vv.y, vv.z])
                o = m.pose.pose.orientation; q.append([o.x, o.y, o.z, o.w])
            else:
                rt.append(tb.to_sec()); rs.append(list(m.angular_velocities))
    t, v, rt, rs = map(np.array, (t, v, rt, rs))
    R = Rotation.from_quat(q); Rm = R.as_matrix() if hasattr(R, "as_matrix") else R.as_dcm()
    acc = np.gradient(v, t, axis=0)                       # world acceleration
    spec = acc + np.array([0, 0, 9.81])                    # specific force needed (m = 1)
    thrust_real = np.einsum("nij,nj->ni", Rm, np.tile([0, 0, 1.0], (len(t), 1)))
    f_real = np.einsum("ni,ni->n", spec, thrust_real)      # along body z
    idx = np.clip(np.searchsorted(rt, t) - 1, 0, len(rt) - 1)
    f_cmd = cf * np.sum(rs[idx] * np.abs(rs[idx]), axis=1)
    k = f_cmd > 12                                          # high-thrust moments
    print(path.split("/")[-1])
    print(f"  rotor command range {rs.min():.0f} .. {rs.max():.0f} rad/s; |omega| percentiles 50/90/99: "
          + " / ".join(f"{np.percentile(np.abs(rs), p):.0f}" for p in (50, 90, 99)))
    print(f"  commanded thrust >12 N at {k.mean()*100:.1f}% of samples; there realised/commanded = "
          f"{np.median(f_real[k] / f_cmd[k]):.2f} (median)")
    for lo, hi in [(10, 14), (14, 18), (18, 25), (25, 40), (40, 1e9)]:
        kk = (f_cmd >= lo) & (f_cmd < hi)
        if kk.sum() > 5:
            print(f"    cmd {lo:>4}-{hi if hi < 1e8 else 'inf':>4} N: realised median {np.median(f_real[kk]):5.1f} N  (n={kk.sum()})")
