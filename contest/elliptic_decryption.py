from dataclasses import dataclass

p = 2 ** 256 - 2 ** 224 + 2 ** 192 + 2 ** 96 - 1


@dataclass
class Zp:
    val: int

    def __pow__(self, order: int):
        return Zp(pow(self.val, order, p))

    def __truediv__(self, other):
        return self * (other ** -1)

    def __neg__(self):
        return Zp(p - self.val % p)

    def __add__(self, other):
        return Zp((self.val + other.val) % p)

    def __mul__(self, other):
        return Zp((self.val * other.val) % p)

    def __sub__(self, other):
        return self + -other


a = Zp(p - 3)
b = Zp(41058363725152142129326129780047268409114441015993725554835256314039467401291)


@dataclass
class Point:
    x: Zp
    y: Zp
    z: Zp

    def is_unit(self):
        return self.z == 0

    def __pow__(self, order: int):
        if order < 0:
            return -self ** -order
        res = unit()
        while order != 0:
            if order % 2 == 0:
                self = self * self
                order //= 2
            else:
                res = res * self
                order -= 1
        return res

    def __truediv__(self, other):
        return self * -other

    def __neg__(self):
        return Point(self.x, -self.y, self.z)

    def __eq__(self, other) -> bool:
        #if self.is_unit() or other.is_unit():
        #    return self.is_unit() and other.is_unit()
        return self.x * other.z == other.x * self.z \
            and self.y * other.z == other.y * self.z

    def __mul__(self, other):
        if self == unit():
            return other
        elif other == unit():
            return self
        elif self == -other:
            return unit()
        elif self == other:
            x, y, z = self.x, self.y, self.z
            q = Zp(2) * y * z
            n = Zp(3) * x ** 2 + a * z ** 2
            p = Zp(4) * x * y ** 2 * z
            u = n ** 2 - Zp(2) * p
            new_x = u * q
            new_z = q ** 3
            new_y = n * (p - u) - Zp(8) * y ** 4 * z ** 2
            return Point(new_x, new_y, new_z)
        else:
            u = self.z * other.y - self.y * other.z
            v = self.z * other.x - self.x * other.z
            w = u ** 2 * self.z * other.z - v ** 3 \
                - Zp(2) * v ** 2 * self.x * other.z
            new_x = v * w
            new_y = u * (v ** 2 * self.x * other.z - w) \
                    - v ** 3 * self.y * other.z
            new_z = v ** 3 * self.z * other.z
            return Point(new_x, new_y, new_z)


def unit():
    return Point(Zp(0), Zp(1), Zp(0))


s = int(input())
n = int(input())


def read_point(line: str):
    line = line.rstrip('\n')
    if line == 'Z':
        return unit()
    else:
        x, y = line.split(' ')
        return Point(Zp(int(x)), Zp(int(y)), Zp(1))


code = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_.'


def encode(x: int):
    res = ''
    while x != 0:
        res += code[x % 64]
        x //= 64
    return res


for _ in range(n):
    c1 = read_point(input())
    c2 = read_point(input())
    d = c2 / (c1 ** s)
    print(encode((d.x / d.z).val))
