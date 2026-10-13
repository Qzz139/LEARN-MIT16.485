#!/usr/bin/env python3
"""Deliverable 1 check: single-segment minimum-velocity QPs  min p^T Q p  s.t.  A p = b.

P(t) = sum_{k=1..N} p_k t^k (p_0 = 0 from P(0) = 0), cost = int_0^1 P'(t)^2 dt.
Q_ij = int_0^1 (i t^(i-1)) (j t^(j-1)) dt = i j / (i + j - 1), solved through the KKT system.
"""
from fractions import Fraction

import numpy as np


def Q_matrix(N):
    return np.array([[i * j / (i + j - 1) for j in range(1, N + 1)] for i in range(1, N + 1)])


def Q_exact(N):
    return [[Fraction(i * j, i + j - 1) for j in range(1, N + 1)] for i in range(1, N + 1)]


def solve_qp(Q, A, b):
    n, m = Q.shape[0], A.shape[0]
    K = np.block([[2 * Q, A.T], [A, np.zeros((m, m))]])
    sol = np.linalg.solve(K, np.concatenate([np.zeros(n), b]))
    p = sol[:n]
    return p, p @ Q @ p


def report(title, N, rows, rhs):
    Q = Q_matrix(N)
    A = np.array(rows, dtype=float)
    b = np.array(rhs, dtype=float)
    p, J = solve_qp(Q, A, b)
    terms = " ".join(f"{c:+.4f} t^{k}" for k, c in reversed(list(enumerate(p, start=1))) if abs(c) > 1e-9)
    print(f"{title}: N = {N}")
    print("  Q =", [[str(v) for v in row] for row in Q_exact(N)])
    print("  A =", rows, " b =", rhs)
    print(f"  p* = {np.round(p, 6).tolist()}   P*(t) = {terms}   J* = {J:.6f}")


# P(1) = 1  ->  sum_k p_k = 1
report("Q1 degree 1", 1, [[1]], [1])
report("Q2 degree 2", 2, [[1, 1]], [1])
report("Q3 degree 3", 3, [[1, 1, 1]], [1])
# extra constraint P'(1) = -2  ->  sum_k k p_k = -2
report("Q4a degree 2 + P'(1)=-2", 2, [[1, 1], [1, 2]], [1, -2])
report("Q4b degree 3 + P'(1)=-2", 3, [[1, 1, 1], [1, 2, 3]], [1, -2])

print("\nExtra: optimal cost with P'(1) = -2 as the degree grows (infimum over all P is 1, never attained)")
for N in [2, 3, 4, 5, 7, 10, 15]:
    rows = [[1] * N, list(range(1, N + 1))]
    _, J = solve_qp(Q_matrix(N), np.array(rows, float), np.array([1.0, -2.0]))
    print(f"  N = {N:2d}: J* = {J:.6f}")
