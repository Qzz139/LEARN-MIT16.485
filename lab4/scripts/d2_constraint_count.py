#!/usr/bin/env python3
"""Deliverable 2 check: build the constraint system of a k-segment minimum-r trajectory.

Each segment is a degree 2r-1 polynomial (2r unknowns), so there are 2rk unknowns.
Constraints:
  waypoint (position) constraints : both ends of every segment            -> 2k
  free-derivative (continuity)    : derivatives 1..2r-2 at k-1 interior    -> (2r-2)(k-1)
  fixed-derivative constraints    : derivatives 1..r-1 at start and at end -> 2(r-1)
The script assembles these rows for random segment durations and checks the
matrix is square and full rank, i.e. the trajectory is uniquely determined.
"""
import math

import numpy as np


def deriv_row(n_coef, order, t):
    """Row giving d^order/dt^order of sum_j c_j t^j evaluated at t."""
    row = np.zeros(n_coef)
    for j in range(order, n_coef):
        row[j] = math.factorial(j) / math.factorial(j - order) * t ** (j - order)
    return row


def build(k, r, rng):
    n = 2 * r                      # coefficients per segment (degree 2r-1)
    T = rng.uniform(0.5, 2.0, k)   # segment durations, local time in [0, T_i]
    rows, kinds = [], []

    def put(seg_rows):
        full = np.zeros(n * k)
        for seg, row in seg_rows:
            full[seg * n:(seg + 1) * n] += row
        rows.append(full)

    for i in range(k):             # waypoint constraints at both ends of each segment
        put([(i, deriv_row(n, 0, 0.0))]); kinds.append("waypoint")
        put([(i, deriv_row(n, 0, T[i]))]); kinds.append("waypoint")
    for i in range(k - 1):         # continuity of derivatives 1..2r-2 at interior points
        for d in range(1, 2 * r - 1):
            put([(i, deriv_row(n, d, T[i])), (i + 1, -deriv_row(n, d, 0.0))]); kinds.append("free-derivative")
    for d in range(1, r):          # fixed derivatives 1..r-1 at start and end
        put([(0, deriv_row(n, d, 0.0))]); kinds.append("fixed-derivative")
        put([(k - 1, deriv_row(n, d, T[-1]))]); kinds.append("fixed-derivative")
    M = np.array(rows)
    return M, {s: kinds.count(s) for s in ("waypoint", "free-derivative", "fixed-derivative")}


rng = np.random.default_rng(0)
print(" r  k | unknowns | waypoint  free-deriv  fixed-deriv | rows  rank")
for r in (4, 2, 3, 5):
    for k in (1, 2, 3, 5):
        M, c = build(k, r, rng)
        print(f"{r:2d} {k:2d} | {M.shape[1]:8d} | {c['waypoint']:8d} {c['free-derivative']:11d} {c['fixed-derivative']:12d} |"
              f" {M.shape[0]:4d} {np.linalg.matrix_rank(M):5d}")
print("formula: 2k + (2r-2)(k-1) + 2(r-1) = 2rk  (min snap r=4: 2k + 6(k-1) + 6 = 8k)")
