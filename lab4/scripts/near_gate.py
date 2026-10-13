import csv, math
F = "/home/qz/vnav-builds/lab4/lab4_Data/StreamingAssets/vnav-2020-lab4_static_tfs.csv"
rows = [r for r in csv.reader(open(F)) if len(r) >= 8]
g0 = next(r for r in rows if r[0] == "red_square_drone_door")
gx, gy, gz = map(float, g0[1:4])          # Unity coordinates (y up)
print("gate 0 (unity):", gx, gy, gz, " quat:", g0[4:8])
near = []
for r in rows:
    x, y, z = map(float, r[1:4])
    d = math.dist((x, y, z), (gx, gy, gz))
    if d < 3.0 and r is not g0:
        near.append((d, r[0], round(x - gx, 3), round(y - gy, 3), round(z - gz, 3)))
for item in sorted(near)[:25]:
    print("%.2f m  %-30s  d(unity x,y,z) = %s" % (item[0], item[1], item[2:]))
print("distinct object names:", len({r[0].split(' (')[0] for r in rows}))
print(sorted({r[0].split(' (')[0] for r in rows})[:80])
