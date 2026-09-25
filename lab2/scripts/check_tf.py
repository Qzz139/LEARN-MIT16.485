#!/usr/bin/env python3
"""Sample the av1/av2 transforms from tf and compare them with the analytic model.

Usage (with the two-drone scenario running):
    python3 check_tf.py [duration_s] [out.csv]

For every sample the three transforms world->av1, world->av2 and av1->av2 are
looked up at the same timestamp. The phase t of AV1 on its circle is recovered
as atan2(y1, x1), which equals the elapsed time modulo 2*pi, and is used to
evaluate the closed-form expressions derived in the report.
"""
import csv
import math
import sys

import rospy
import tf2_ros

SQRT5 = math.sqrt(5.0)


def yaw_of(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def main():
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
    out_path = sys.argv[2] if len(sys.argv) > 2 else "tf_samples.csv"

    rospy.init_node("check_tf", anonymous=True)
    buf = tf2_ros.Buffer()
    tf2_ros.TransformListener(buf)
    rospy.sleep(1.0)

    rows = []
    last_stamp = None
    rate = rospy.Rate(25)
    end = rospy.Time.now() + rospy.Duration(duration)
    while not rospy.is_shutdown() and rospy.Time.now() < end:
        try:
            w1 = buf.lookup_transform("world", "av1", rospy.Time(0))
            stamp = w1.header.stamp
            w2 = buf.lookup_transform("world", "av2", stamp)
            r12 = buf.lookup_transform("av1", "av2", stamp)
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException):
            rate.sleep()
            continue
        if stamp == last_stamp:
            rate.sleep()
            continue
        last_stamp = stamp

        p1, q1 = w1.transform.translation, w1.transform.rotation
        p2, q2 = w2.transform.translation, w2.transform.rotation
        pr = r12.transform.translation
        t = math.atan2(p1.y, p1.x)
        s, c = math.sin(t), math.cos(t)

        # Analytic relative position o_2^1(t) and plane coordinates o_2^p.
        ax, ay, az = s * c - 1.0, -s * s, math.cos(2.0 * t)
        xp = pr.x + 1.0
        yp = ((pr.y + 0.5) + 2.0 * pr.z) / SQRT5
        zp = (-2.0 * (pr.y + 0.5) + pr.z) / SQRT5

        rows.append({
            "stamp": stamp.to_sec(), "t_mod_2pi": t,
            "av1_circle": p1.x ** 2 + p1.y ** 2 - 1.0, "av1_z": p1.z,
            "av1_yaw_minus_t": wrap(yaw_of(q1) - t),
            "av1_roll_pitch_q": math.hypot(q1.x, q1.y),
            "av2_y": p2.y, "av2_parabola": p2.z - (1.0 - 2.0 * p2.x ** 2),
            "av2_rot_angle": 2.0 * math.acos(min(1.0, abs(q2.w))),
            "rel_x": pr.x, "rel_y": pr.y, "rel_z": pr.z,
            "rel_err": math.sqrt((pr.x - ax) ** 2 + (pr.y - ay) ** 2 + (pr.z - az) ** 2),
            "plane": pr.z - 2.0 * pr.y - 1.0,
            "xp": xp, "yp": yp, "zp": zp,
            "ellipse": xp ** 2 / 0.25 + yp ** 2 / 1.25 - 1.0,
        })
        rate.sleep()

    if not rows:
        print("no samples collected")
        return 1
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    span = rows[-1]["stamp"] - rows[0]["stamp"]
    print("samples: %d over %.2f s -> %s" % (len(rows), span, out_path))
    checks = [
        ("av1_circle", "AV1: x^2 + y^2 - 1"),
        ("av1_z", "AV1: z"),
        ("av1_yaw_minus_t", "AV1: yaw - atan2(y, x)  [rad]"),
        ("av1_roll_pitch_q", "AV1: |(q_x, q_y)| (roll/pitch part)"),
        ("av2_y", "AV2: y"),
        ("av2_parabola", "AV2: z - (1 - 2 x^2)"),
        ("av2_rot_angle", "AV2: rotation angle  [rad]"),
        ("rel_err", "av1->av2 vs analytic o_2^1(t)  [m]"),
        ("plane", "av1->av2: z - 2y - 1"),
        ("zp", "plane frame: z_p"),
        ("ellipse", "plane frame: x_p^2/(1/4) + y_p^2/(5/4) - 1"),
    ]
    for key, label in checks:
        print("max |%s| = %.2e" % (label, max(abs(r[key]) for r in rows)))
    # The phase must advance at 1 rad/s if "time" in the publisher is elapsed seconds.
    stamps = [r["stamp"] for r in rows]
    phase = [rows[0]["t_mod_2pi"]]
    for r in rows[1:]:
        phase.append(phase[-1] + wrap(r["t_mod_2pi"] - phase[-1]))
    ms, mp = sum(stamps) / len(stamps), sum(phase) / len(phase)
    slope = (sum((a - ms) * (b - mp) for a, b in zip(stamps, phase))
             / sum((a - ms) ** 2 for a in stamps))
    print("AV1 phase rate d(atan2(y, x))/d(stamp) = %.6f rad/s" % slope)
    print("x_p range: [%.4f, %.4f]   y_p range: [%.4f, %.4f]" % (
        min(r["xp"] for r in rows), max(r["xp"] for r in rows),
        min(r["yp"] for r in rows), max(r["yp"] for r in rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
