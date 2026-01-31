#!/bin/env python

import psutil
import sys
from time import sleep
from filterpy.kalman import KalmanFilter
import numpy as np

f = KalmanFilter(dim_x=2, dim_z=1)
f_fast = KalmanFilter(dim_x=2, dim_z=1)

f.x = np.array([[0.0], [0.0]])
f.F = np.array([[1.0, 1 / 600], [0.0, 1.0]])
f.H = np.array([[1, 0.0]])
f.P *= 10 * 1024**3
f.Q = np.array([[1024.0, 0], [0, 1024**2 / 200]])
f.R *= 250 * 1024**2

f_fast.x = np.array([[0.0], [0.0]])
f_fast.F = np.array([[1.0, 1 / 600], [0.0, 1.0]])
f_fast.H = np.array([[1, 0.0]])
f_fast.P *= 10 * 1024**3
f_fast.Q = np.array([[1024 * 1024.0, 0], [0, 1024**3 / 200]])
f_fast.R *= 250 * 1024**2


pid = int(sys.argv[1])

proc = psutil.Process(pid)
factor = 10
n = 1
mem = 0
rate = 0
last = 0
c = 0
print_c = 600
sep = 0
spread = 0

while psutil.pid_exists(pid):
    rss = proc.memory_info().rss
    f.predict()
    f.update(rss)

    f_fast.predict()
    f_fast.update(rss)

    mem = f.x[0][0]
    # if abs(mem-rss) > 1.5*1024**3:
    #     f.P = np.array([[10*1024**3, 0], [0, 10*1024**3]])
    rate = f.x[1][0]
    # mem = rss / n + mem*(n-1)/n

    # if n > 1:
    #     d = mem - last
    #     dn = n - 1
    #     rate = d / dn + rate * (dn - 1) / dn

    # last = mem

    c += 1
    if c < print_c:
        sys.stdout.write("\r")
    else:
        c = 0
        sys.stdout.write("\n")

    x_p = f.P[0][0]
    dx_p = f.P[1][1]

    x_pf = f_fast.P[0][0]
    dx_pf = f_fast.P[1][1]

    tx_p = ((x_p**2) + (x_pf**2)) ** 0.5

    spread = ((n - 1) / n) * spread + (1 / n) * (f.x[0][0] - f_fast.x[0][0])

    sep = spread / (tx_p)

    if n == factor and abs(sep) > 3:
        # new_f_P = (spread**2/9 - f_fast.P[0][0]**2)
        # m = new_f_P  / f.P[0][0]
        # f.P[0][0] *= m
        n = 1
        f.P = f_fast.P
        f.x = f_fast.x
    # asep = abs(sep)
    # f.P = (f_fast.P*(asep) + f.P*(5 - asep)) * 0.2

    sys.stdout.write(
        f"{int(mem / (1024**2))} M  {int(rate / (1024**2))} M/min  s({int(x_p**0.5 / 1024)} {int(dx_p / 1024**2)}) f({int(x_pf / 1024**2)} {int(dx_pf / 1024**2)}) spread = {int(spread / 1024**2)} sep = {sep:.1f}         "
    )

    if n < factor:
        n += 1

    sleep(0.1)

sys.stdout.write("\n")
