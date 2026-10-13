"""Oscillation summary for unstable runs: python3 osc_check.py a.bag [b.bag ...]

Dominant frequency of the position deviation (after 8 s), body-rate RMS and rotor-command range.
"""
import sys, numpy as np, rosbag
for path in sys.argv[1:]:
    t, p, w = [], [], []
    rt, rs = [], []
    with rosbag.Bag(path) as bag:
        for topic, m, tb in bag.read_messages(topics=["/current_state", "/rotor_speed_cmds"]):
            if topic == "/current_state":
                t.append(m.header.stamp.to_sec()); pp = m.pose.pose.position; p.append([pp.x, pp.y, pp.z])
                a = m.twist.twist.angular; w.append([a.x, a.y, a.z])
            else:
                rt.append(tb.to_sec()); rs.append(list(m.angular_velocities))
    t, p, w, rs = map(np.array, (t, p, w, rs))
    k = t - t[0] > 8
    print(path.split("/")[-1])
    for i, ax in enumerate("xyz"):
        s = p[k, i] - p[k, i].mean()
        f = np.fft.rfftfreq(len(s), np.mean(np.diff(t)))
        F = np.abs(np.fft.rfft(s)); j = np.argmax(F[1:]) + 1
        print(f"  {ax}: std {s.std():.3f} m, dominant {f[j]:.2f} Hz")
    print(f"  |omega_world| rms {np.sqrt(np.mean(np.sum(w[k]**2,1))):.2f} rad/s")
    print(f"  rotor cmd: min {rs.min():.1f}, max {rs.max():.1f}, mean {rs.mean():.1f} rad/s, frac<0 {np.mean(rs<0):.3f}")
