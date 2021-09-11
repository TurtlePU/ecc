from dataclasses import dataclass
from typing import Optional, Tuple
from algebra_base import Group, Field, SqrtField
from encoders import Encoder
from random import randrange


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

    def intern(self, p: Point) -> Tuple[int, int]:
        if p.z == 0:
            raise Zero
        else:
            z = self.field.inv(p.z)
            return self.field.mul(p.x, z), self.field.mul(p.y, z)


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
            return self.into(Point(new_x, new_y, new_z))
        else:
            u = a.z * b.y - a.y * b.z
            v = a.z * b.x - a.x * b.z
            w = u ** 2 * a.z * b.z - v ** 3 - 2 * v ** 2 * a.x * b.z
            new_x = v * w
            new_y = u * (v ** 2 * a.x * b.z - w) - v ** 3 * a.y * b.z
            new_z = v ** 3 * a.z * b.z
            return self.into(Point(new_x, new_y, new_z))


class RandomEncoder(Encoder[Point]):
    def __init__(self, primary: Encoder[int], curve: SolvableCurve, rand_shift: int):
        self.primary = primary
        self.curve = curve
        self.rand_shift = rand_shift

    def encode(self, text):
        nums = self.primary.encode(text)
        return [self.encode_one(num) for num in nums]

    def decode(self, code):
        nums = [self.decode_one(code) for code in code]
        return self.primary.decode(nums)

    def encode_one(self, num: int) -> Point:
        while True:
            point = self.curve.solve_for_x(num + self.random())
            if point is not None:
                return point

    def random(self) -> int:
        return randrange(0, 1 << self.rand_shift) << self.rand_shift

    def decode_one(self, code: Point) -> int:
        return code.x & (1 << self.rand_shift - 1)


@dataclass
class PartialEncoder(Encoder[Point]):
    x_enc: Encoder[int]
    curve: SolvableCurve

    def encode(self, text):
        return [ self.curve.asserted(x) for x in self.x_enc.encode(text) ]

    def decode(self, code):
        return self.x_enc.decode([ self.curve.intern(p)[0] for p in code ])
