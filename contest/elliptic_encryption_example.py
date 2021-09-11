from elliptic_curve import *
from prime_fields import *

p = 2 ** 256 - 2 ** 224 + 2 ** 192 + 2 ** 96 - 1
a = -3
b = 41058363725152142129326129780047268409114441015993725554835256314039467401291
gx = 48439561293906451759052585252797914202762949526041747995844080717082404635286
gy = 36134250956749795798585127919587881956611106672985015071877198253568414405109
order = 115792089210356248762697446949407573529996955224135760342422259061068512044369

curve = Curve(Zn(p), a, b)
group = E(order, curve)

from sys import stderr

s = int(input())
k = curve.intern(group.pow(curve.point(gx, gy), s))
ans = '{} {}\n'.format(*k)

n = int(input())
ans += '{}\n'.format(n)

for _ in range(n):
    ans += '{}\n'.format(input())

print(ans, file=stderr)
print('==============', file=stderr)
print(ans)
