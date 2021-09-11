from elliptic_curve import *
from prime_fields import *
from gamal import *
from encoders import *

p = 2 ** 256 - 2 ** 224 + 2 ** 192 + 2 ** 96 - 1
a = -3
b = 41058363725152142129326129780047268409114441015993725554835256314039467401291
gx = 48439561293906451759052585252797914202762949526041747995844080717082404635286
gy = 36134250956749795798585127919587881956611106672985015071877198253568414405109
order = 115792089210356248762697446949407573529996955224135760342422259061068512044369

curve = SolvableCurve(Zn(p), a, b)
group = E(order, curve)
generator = curve.point(gx, gy)
gamal = ElGamal(group, generator, PartialEncoder(LineEncoder(Base64()), curve))

from sys import stderr

s = int(input())
ans = '{}\n'.format(s)
k = group.pow(generator, s)

n = int(input())
ans += '{}\n'.format(n)

message = '\n'.join(input() for _ in range(n))

for c1, c2 in gamal.encrypt(k, message):
    ans += '{} {}\n{} {}\n'.format(*curve.intern(c1), *curve.intern(c2))

print(ans, file=stderr)
print(ans)
