import csv, math, re
F = "/home/qz/vnav-builds/lab4/lab4_Data/StreamingAssets/vnav-2020-lab4_static_tfs.csv"
gates = {}
for row in csv.reader(open(F)):
    m = re.fullmatch(r"red_square_drone_door(?: \((\d+)\))?", row[0])
    if m:
        x, y, z, qx, qy, qz, qw = map(float, row[1:8])
        # same unity -> ROS conversion as traj_vertices_publisher.cpp
        p = (x, z, y); q = (-qx, -qz, -qy, qw)
        gates[int(m.group(1) or 0)] = (p, q)
def rpy(q):
    x, y, z, w = q
    r = math.atan2(2*(w*x+y*z), 1-2*(x*x+y*y)); pch = math.asin(max(-1, min(1, 2*(w*y-z*x)))); yw = math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))
    return [math.degrees(a) for a in (r, pch, yw)]
print(" i      x       y      z  | roll  pitch   yaw  | dir->next  dist")
keys = sorted(gates)
for k, i in enumerate(keys):
    p, q = gates[i]; r, pc, yw = rpy(q)
    if k + 1 < len(keys):
        pn = gates[keys[k+1]][0]; d = math.degrees(math.atan2(pn[1]-p[1], pn[0]-p[0])); dist = math.dist(p, pn)
        nxt = f"{d:8.1f} {dist:6.1f}"
    else: nxt = "    (end)"
    print(f"{i:2d} {p[0]:7.2f} {p[1]:7.2f} {p[2]:6.2f} | {r:5.1f} {pc:5.1f} {yw:7.1f} | {nxt}")
tot = sum(math.dist(gates[keys[k]][0], gates[keys[k+1]][0]) for k in range(len(keys)-1))
print(f"total gate-to-gate path length (straight lines): {tot:.1f} m")
