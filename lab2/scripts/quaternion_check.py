#!/usr/bin/env python3
"""Numerical sanity check of the Omega_1 / Omega_2 properties (not a proof).

Quaternions are q = (q1, q2, q3, q4) with the scalar q4 last, as in the lab handout.
Also tests the Omega_1 printed in the lecture slides, whose (1,3) and (2,3) entries
have the opposite sign.
"""
import numpy as np


def omega1(q):
    q1, q2, q3, q4 = q
    return np.array([[q4, -q3, q2, q1], [q3, q4, -q1, q2], [-q2, q1, q4, q3], [-q1, -q2, -q3, q4]])


def omega1_slides(q):
    q1, q2, q3, q4 = q
    return np.array([[q4, -q3, -q2, q1], [q3, q4, q1, q2], [-q2, q1, q4, q3], [-q1, -q2, -q3, q4]])


def omega2(q):
    q1, q2, q3, q4 = q
    return np.array([[q4, q3, -q2, q1], [-q3, q4, q1, q2], [q2, -q1, q4, q3], [-q1, -q2, -q3, q4]])


def main():
    rng = np.random.default_rng(0)
    I = np.eye(4)
    identity_q = np.array([0.0, 0.0, 0.0, 1.0])
    worst = dict.fromkeys(["orth", "ident", "prod", "comm", "comm_T", "slides"], 0.0)
    trials = 1000
    for _ in range(trials):
        q = rng.normal(size=4)
        q /= np.linalg.norm(q)  # unit quaternion
        x, y = rng.normal(size=4), rng.normal(size=4)  # arbitrary, not unit
        for m in (omega1(q), omega2(q)):
            # 1. Orthogonality: Omega^T Omega = Omega Omega^T = I for a unit q.
            worst["orth"] = max(worst["orth"], abs(m.T @ m - I).max(), abs(m @ m.T - I).max())
            # 2. Omega(q)^T q is the identity quaternion.
            worst["ident"] = max(worst["ident"], abs(m.T @ q - identity_q).max())
        # 3. Both matrices give the same product x * y, and Omega_1(x), Omega_2(y) commute.
        a, b = omega1(x), omega2(y)
        worst["prod"] = max(worst["prod"], abs(a @ y - b @ x).max())
        worst["comm"] = max(worst["comm"], abs(a @ b - b @ a).max())
        worst["comm_T"] = max(worst["comm_T"], abs(a @ b.T - b.T @ a).max())
        s = omega1_slides(q)
        worst["slides"] = max(worst["slides"], abs(s.T @ s - I).max())

    print("random trials: %d (q unit, x and y arbitrary)" % trials)
    print("max |Omega_i(q)^T Omega_i(q) - I|, |Omega_i Omega_i^T - I| = %.2e" % worst["orth"])
    print("max |Omega_i(q)^T q - [0,0,0,1]|                          = %.2e" % worst["ident"])
    print("max |Omega_1(x) y - Omega_2(y) x|                         = %.2e" % worst["prod"])
    print("max |Omega_1(x) Omega_2(y) - Omega_2(y) Omega_1(x)|       = %.2e" % worst["comm"])
    print("max |Omega_1(x) Omega_2(y)^T - Omega_2(y)^T Omega_1(x)|   = %.2e" % worst["comm_T"])
    print("slides' Omega_1: max |Omega_1^T Omega_1 - I|              = %.4f" % worst["slides"])


if __name__ == "__main__":
    main()
