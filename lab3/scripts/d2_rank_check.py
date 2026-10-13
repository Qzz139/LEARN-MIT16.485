#!/usr/bin/env python3
"""Numerical check for Deliverable 2A (not a proof): rank of the rotor-to-wrench map F.

Top view, x right / y up, a = d/sqrt(2). Rotors: 1 top-left, 2 bottom-left,
3 bottom-right, 4 top-right. A rotor spinning CCW (seen from above) pushes the
body with a CW reaction torque, so its yaw entry is -c_d; a CW rotor gives +c_d.
"""
import numpy as np

cf, cd, d = 1e-3, 1e-5, 0.3
a = d / np.sqrt(2)
pos = np.array([[-a, a], [-a, -a], [a, -a], [a, a]])  # rotors 1..4


def F_matrix(spin):
    """spin[i] = +1 for CCW, -1 for CW (seen from above)."""
    thrust = cf * np.ones(4)
    tau_x = cf * pos[:, 1]          # y_i * f_i
    tau_y = -cf * pos[:, 0]         # -x_i * f_i
    tau_z = -cd * np.asarray(spin)  # reaction torque
    return np.vstack([thrust, tau_x, tau_y, tau_z])


for name, spin in [("(a) original", [+1, -1, +1, -1]), ("(b) rotors 3,4 reversed", [+1, -1, -1, +1])]:
    F = F_matrix(spin)
    print(f"{name}: spin(1..4, +1=CCW) = {spin}")
    print(np.array2string(F, precision=6, suppress_small=False))
    print(f"  rank = {np.linalg.matrix_rank(F)}, singular values = {np.linalg.svd(F, compute_uv=False)}")
    if np.linalg.matrix_rank(F) < 4:
        # yaw row is a multiple of the roll row -> tau_z = k * tau_x for every input
        k = F[3] @ F[1] / (F[1] @ F[1])
        print(f"  tau_z row = {k:.6f} * tau_x row, residual = {np.linalg.norm(F[3] - k * F[1]):.2e}")
        # pure yaw torque [0, 0, 0, 1] is not reachable: least-squares residual > 0
        w = np.array([0, 0, 0, 1.0])
        u, *_ = np.linalg.lstsq(F, w, rcond=None)
        print(f"  best achievable wrench for target [0,0,0,1]: {F @ u}, residual = {np.linalg.norm(F @ u - w):.3f}")
    print()
