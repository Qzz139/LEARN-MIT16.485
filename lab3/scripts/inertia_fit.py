"""Fit the simulator's effective inertia: tau_cmd(t - delay) = J_true * domega_body/dt (per axis)."""
import sys, numpy as np, rosbag
from scipy.spatial.transform import Rotation
cf, cd, d = 1e-3, 1e-5, 0.3
l = d * cf / np.sqrt(2)
F2W = np.array([[cf, cf, cf, cf], [l, l, -l, -l], [-l, l, l, -l], [cd, -cd, cd, -cd]])
path = sys.argv[1]
t, q, w, rt, rs = [], [], [], [], []
with rosbag.Bag(path) as bag:
    for topic, m, tb in bag.read_messages(topics=["/current_state", "/rotor_speed_cmds"]):
        if topic == "/current_state":
            # header stamps are evenly spaced (20 ms); bag receive times can repeat
            t.append(m.header.stamp.to_sec()); o = m.pose.pose.orientation; q.append([o.x, o.y, o.z, o.w])
            a = m.twist.twist.angular; w.append([a.x, a.y, a.z])
        else:
            rt.append(tb.to_sec()); rs.append(list(m.angular_velocities))
t, w, rt, rs = map(np.array, (t, w, rt, rs))
R = Rotation.from_quat(q); Rm = R.as_matrix() if hasattr(R, "as_matrix") else R.as_dcm()
wb = np.einsum("nji,nj->ni", Rm, w)              # R^T w_world
alpha = (wb[2:] - wb[:-2]) / (t[2:] - t[:-2])[:, None]
tc = t[1:-1]
wrench = (F2W @ (rs * np.abs(rs)).T).T            # [f, tx, ty, tz] commanded
print(path.split("/")[-1], f"{len(t)} states, {len(rt)} commands")
best = None
for delay in np.arange(0.0, 0.16, 0.02):
    idx = np.searchsorted(rt, tc - delay, side="right") - 1
    ok = idx >= 0
    tau = wrench[idx[ok], 1:]; al = alpha[ok]
    J = np.sum(tau * al, 0) / np.sum(al * al)
    res = tau - al * J
    r2 = 1 - np.sum(res ** 2, 0) / np.sum((tau - tau.mean(0)) ** 2, 0)
    print(f"  delay {delay*1e3:5.0f} ms: J = [{J[0]:.4f}, {J[1]:.4f}, {J[2]:.4f}]  R2 = [{r2[0]:.2f}, {r2[1]:.2f}, {r2[2]:.2f}]")
