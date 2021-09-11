from typing import Generic, List, Optional, Tuple, TypeVar
from dataclasses import dataclass
from random import randrange

T = TypeVar('T')


class Group(Generic[T]):
    def eq(self, x: T, y: T) -> bool:
        raise NotImplementedError

    def order(self) -> int:
        raise NotImplementedError

    def into(self, x: T) -> T:
        return x

    def mul(self, x: T, y: T) -> T:
        raise NotImplementedError

    def unit(self) -> T:
        raise NotImplementedError

    def inv(self, x: T) -> T:
        raise NotImplementedError

    def true_div(self, x: T, y: T) -> T:
        return self.mul(x, self.inv(y))

    def pow(self, x: T, ord: int) -> T:
        result = self.unit()
        while ord > 0:
            if ord & 1 == 0:
                x = self.mul(x, x)
                ord >>= 1
            else:
                result = self.mul(result, x)
                ord ^= 1
        return result


class Field(Group[T]):
    def add(self, x: T, y: T) -> T:
        raise NotImplementedError

    def zero(self) -> T:
        raise NotImplementedError

    def is_zero(self, x: T) -> bool:
        return self.eq(x, self.zero())

    def neg(self, x: T) -> T:
        raise NotImplementedError

    def sub(self, x: T, y: T) -> T:
        return self.add(x, self.neg(y))


class SqrtField(Field[T]):
    def sqrt(self, x: T) -> Optional[T]:
        raise NotImplementedError


@dataclass
class Zn(SqrtField[int]):
    N: int

    def order(self):
        return self.N

    def into(self, x):
        return x % self.N

    def eq(self, x, y):
        return (x - y) % self.N == 0

    def mul(self, x, y):
        return (x * y) % self.N

    def unit(self):
        return 1

    def inv(self, x):
        return int(pow(x, -1, self.N))

    def pow(self, x, ord):
        return int(pow(x, ord, self.N))

    def add(self, x, y):
        return (x + y) % self.N

    def zero(self):
        return 0

    def neg(self, x):
        return self.N - x % self.N

    def sqrt(self, x):
        assert self.N % 4 == 3
        sqrt = self.pow(x, (self.N + 1) // 4)
        if self.into(sqrt ** 2) == self.into(x):
            return sqrt
        else:
            return None


T = TypeVar('T')


class Encoder(Generic[T]):
    def encode(self, text: str) -> List[T]:
        raise NotImplementedError

    def decode(self, code: List[T]) -> str:
        raise NotImplementedError


def chunks(it, n):
    for i in range(0, len(it), n):
        yield it[i:i+n]


def dec_char(number):
    if 0 <= number <= 9:
        return chr(48 + number)
    if 10 <= number <= 35:
        return chr(55 + number)
    if 36 <= number <= 61:
        return chr(61 + number)
    if number == 62:
        return '_'
    if number == 63:
        return '.'
    raise Exception()


def enc_char(ch):
    symbol = ord(ch)
    if 48 <= symbol <= 57:
        return symbol - 48
    if 65 <= symbol <= 90:
        return symbol - 55
    if 97 <= symbol <= 122:
        return symbol - 61
    if symbol == ord('_'):
        return 62
    if symbol == 46:
        return 63
    raise Exception()


def encode_base64(text):
    bigint = 0
    for c in reversed(text):
        bigint = bigint * 64 + enc_char(c)
    return bigint


def decode_base64(code):
    result = ''
    while code != 0:
        result += dec_char(code % 64)
        code //= 64
    return result


class LineEncoder(Encoder[int]):
    def encode(self, text):
        return [ encode_base64(line) for line in text.split('\n') ]

    def decode(self, code):
        return '\n'.join(decode_base64(c) for c in code)


@dataclass
class Point:
    x: int
    y: int
    z: int

    def unpack(self) -> Tuple[int, int, int]:
        return self.x, self.y, self.z


class Zero(Exception):
    pass


@dataclass
class Curve:
    field: Field[int]
    a: int
    b: int

    def point(self, x: int, y: int, z: int = 1) -> Point:
        p = Point(self.field.into(x), self.field.into(y), self.field.into(z))
        assert self.check(p)
        return p

    def rhs(self, x: int, z: int = 1) -> int:
        return x ** 3 + self.a * x * z ** 2 + self.b * z ** 3

    def check(self, p: Point) -> bool:
        x, y, z = p.unpack()
        return self.field.eq(y ** 2 * z, self.rhs(x, z))

    def intern_opt(self, p: Point) -> Optional[Tuple[int, int]]:
        if p.z == 0:
            return None
        else:
            z = self.field.inv(p.z)
            return self.field.mul(p.x, z), self.field.mul(p.y, z)

    def intern(self, p: Point) -> Tuple[int, int]:
        res = self.intern_opt(p)
        if res is None:
            raise Zero
        else:
            return res


class NotOnCurve(Exception):
    pass


class SolvableCurve(Curve):
    def __init__(self, field: SqrtField[int], a: int, b: int):
        super().__init__(field, a, b)

    def solve_for_x(self, x: int) -> Optional[Point]:
        y_sq = self.field.into(self.rhs(x))
        y = self.field.sqrt(y_sq)
        if y is not None:
            return self.point(x, y)
        else:
            return None

    def asserted(self, x: int) -> Point:
        p = self.solve_for_x(x)
        if p is None:
            raise NotOnCurve
        else:
            return p


@dataclass
class E(Group[Point]):
    ord: int
    curve: Curve

    def order(self):
        return self.ord

    def into(self, a):
        return self.curve.point(*a.unpack())

    def unit(self):
        return Point(0, 1, 0)

    def is_unit(self, a: Point) -> bool:
        return a.z == 0

    def inv(self, a):
        return Point(a.x, self.curve.field.neg(a.y), a.z)

    def eq(self, a, b):
        eq = self.curve.field.eq
        return eq(a.x * b.z, a.z * b.x) and eq(a.y * b.z, a.z * b.y)

    def mul(self, a, b):
        if self.is_unit(a):
            return b
        elif self.is_unit(b):
            return a
        elif self.eq(a, self.inv(b)):
            return self.unit()
        elif self.eq(a, b):
            x, y, z = a.unpack()
            q = 2 * y * z
            n = 3 * x ** 2 + self.curve.a * z ** 2
            p = 4 * x * y ** 2 * z
            u = n ** 2 - 2 * p
            new_x = u * q
            new_z = q ** 3
            new_y = n * (p - u) - 8 * y ** 4 * z ** 2
            return self.curve.point(new_x, new_y, new_z)
        else:
            u = a.z * b.y - a.y * b.z
            v = a.z * b.x - a.x * b.z
            w = u ** 2 * a.z * b.z - v ** 3 - 2 * v ** 2 * a.x * b.z
            new_x = v * w
            new_y = u * (v ** 2 * a.x * b.z - w) - v ** 3 * a.y * b.z
            new_z = v ** 3 * a.z * b.z
            return self.curve.point(new_x, new_y, new_z)


@dataclass
class PartialEncoder(Encoder[Point]):
    x_enc: Encoder[int]
    curve: SolvableCurve

    def encode(self, text):
        return [self.curve.asserted(x) for x in self.x_enc.encode(text)]

    def decode(self, code):
        return self.x_enc.decode([self.curve.intern(p)[0] for p in code])


T = TypeVar('T')


class ElGamal(Generic[T]):
    def __init__(self, group: Group[T], generator: T, encoder: Encoder[T]):
        self.group = group
        self.generator = generator
        self.encoder = encoder

    def encrypt(self, public_key: T, message: str) -> List[Tuple[T, T]]:
        return [self.encrypt_one(public_key, m) for m in self.encoder.encode(message)]

    def decrypt(self, private_key: int, cipher: List[Tuple[T, T]]) -> str:
        return self.encoder.decode([self.decrypt_one(private_key, c) for c in cipher])

    def encrypt_one(self, h: T, m: T) -> Tuple[T, T]:
        y = randrange(0, self.group.order())
        return self.group.pow(self.generator, y), self.group.mul(self.group.pow(h, y), m)

    def decrypt_one(self, x: int, c: Tuple[T, T]) -> T:
        c1, c2 = c
        return self.group.true_div(c2, self.group.pow(c1, x))


p = 2 ** 256 - 2 ** 224 + 2 ** 192 + 2 ** 96 - 1
a = -3
b = 41058363725152142129326129780047268409114441015993725554835256314039467401291
gx = 48439561293906451759052585252797914202762949526041747995844080717082404635286
gy = 36134250956749795798585127919587881956611106672985015071877198253568414405109
order = 115792089210356248762697446949407573529996955224135760342422259061068512044369

curve = SolvableCurve(Zn(p), a, b)
g = curve.point(gx, gy)
group = E(order, curve)
gamal = ElGamal(group, g, PartialEncoder(LineEncoder(), curve))

from random import randrange
from sys import argv

directory = argv[1]

for i in range(100):
    file = open('{}/{}'.format(directory, i), 'w')
    print(randrange(1, order), file=file)
    n = randrange(100)
    print(n, file=file)
    for j in range(n):
        p = group.pow(g, randrange(1, order))
        print(decode_base64(curve.intern(p)[0]), file=file)
        print(i, j, 'done')
