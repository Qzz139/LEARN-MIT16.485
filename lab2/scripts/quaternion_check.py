#!/usr/bin/env python3
"""Numerical sanity check of the Omega_1 / Omega_2 properties (not a proof).

Quaternions are (q1, q2, q3, q4) with the scalar last, as in the lab handout.
Also evaluates the Omega_1 printed in the lecture slides, whose (1,3) and (2,3)
entries have the opposite sign.
"""
import math
import random


def omega1(q):
    q1, q2, q3, q4 = q
    return [[q4, -q3, q2, q1], [q3, q4, -q1, q2], [-q2, q1, q4, q3], [-q1, -q2, -q3, q4]]


def omega1_slides(q):
    q1, q2, q3, q4 = q
    return [[q4, -q3, -q2, q1], [q3, q4, q1, q2], [-q2, q1, q4, q3], [-q1, -q2, -q3, q4]]


def omega2(q):
    q1, q2, q3, q4 = q
    return [[q4, q3, -q2, q1], [-q3, q4, q1, q2], [q2, -q1, q4, q3], [-q1, -q2, -q3, q4]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def tr(a):
    return [list(r) for r in zip(*a)]


def matvec(a, x):
    return [sum(a[i][k] * x[k] for k in range(4)) for i in range(4)]


def maxdiff(a, b):
    return max(abs(a[i][j] - b[i][j]) for i in range(4) for j in range(4))


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return [c / n for c in v]


def main():
    random.seed(0)
    eye = [[float(i == j) for j in range(4)] for i in range(4)]
    worst = {"orth": 0.0, "ident": 0.0, "prod": 0.0, "comm": 0.0, "comm_T": 0.0}
    slides_orth = 0.0
    trials = 1000
    for _ in range(trials):
        q = unit([random.gauss(0, 1) for _ in range(4)])
        x = [random.gauss(0, 1) for _ in range(4)]  # arbitrary, not unit
        y = [random.gauss(0, 1) for _ in range(4)]
        for om in (omega1, omega2):
            m = om(q)
            worst["orth"] = max(worst["orth"], maxdiff(mul(tr(m), m), eye),
                                maxdiff(mul(m, tr(m)), eye))
            r = matvec(tr(m), q)
            worst["ident"] = max(worst["ident"], max(abs(a - b) for a, b in zip(r, [0, 0, 0, 1])))
        worst["prod"] = max(worst["prod"], max(abs(a - b) for a, b in
                                               zip(matvec(omega1(x), y), matvec(omega2(y), x))))
        worst["comm"] = max(worst["comm"], maxdiff(mul(omega1(x), omega2(y)),
                                                   mul(omega2(y), omega1(x))))
        worst["comm_T"] = max(worst["comm_T"], maxdiff(mul(omega1(x), tr(omega2(y))),
                                                       mul(tr(omega2(y)), omega1(x))))
        m = omega1_slides(q)
        slides_orth = max(slides_orth, maxdiff(mul(tr(m), m), eye))

    print("random trials: %d (q unit, x and y arbitrary)" % trials)
    print("max |Omega_i(q)^T Omega_i(q) - I|, |Omega_i Omega_i^T - I| = %.2e" % worst["orth"])
    print("max |Omega_i(q)^T q - [0,0,0,1]|                          = %.2e" % worst["ident"])
    print("max |Omega_1(x) y - Omega_2(y) x|                         = %.2e" % worst["prod"])
    print("max |Omega_1(x) Omega_2(y) - Omega_2(y) Omega_1(x)|       = %.2e" % worst["comm"])
    print("max |Omega_1(x) Omega_2(y)^T - Omega_2(y)^T Omega_1(x)|   = %.2e" % worst["comm_T"])
    print("slides' Omega_1: max |Omega_1^T Omega_1 - I|              = %.3f" % slides_orth)


if __name__ == "__main__":
    main()
