from typing import List, Tuple
from elliptic_curve import SolvableCurve, E, Point
from prime_fields import Zn

def curve_params(p, a, b):
    f = Zn(p)
    c = SolvableCurve(f, a, b)
    g = None
    n = 1
    for x in range(p):
        y = c.solve_for_x(x)
        if y is None:
            continue
        if g is None:
            g = y
        n += 1
        if y.y != 0:
            n += 1
    if g is None:
        return None
    else:
        return g, n


def sieve(n):
    lp = [0] * (n + 1)
    pr = []
    for i in range(2, n + 1):
        if lp[i] == 0:
            lp[i] = i
            pr.append(i)
        for p in pr:
            if p > lp[i] or p * i > n:
                break
            lp[p * i] = p
    return pr


def test(p, a, b):
    d = -16 * (4 * a ** 3 + 27 * b ** 2)
    return p != 2 and p != 3 and p % 4 == 3 and Zn(p).into(d) != 0


def gen_curves(p):
    for a in range(p):
        for b in range(p):
            if test(p, a, b):
                params = curve_params(p, a, b)
                if params is not None:
                    g, n = params
                    yield E(n, SolvableCurve(Zn(p), a, b)), g


def scan_primes(fro, to):
    for p in sieve(to):
        if p < fro:
            continue
        mx = max(gen_curves(p), default=None, key=lambda ab: ab[0].ord)
        if mx is not None:
            yield mx
