from algebra_base import GcdMixin


class BinaryPoly(GcdMixin[int]):
    def __init__(self, modulo: int):
        self.modulo = modulo

    def add(self, x, y):
        return x ^ y

    def neg(self, x):
        return x

    def sub(self, x, y):
        return self.add(x, y)

    def zero(self):
        return 0

    def into(self, x):
        while True:
            shift = x.bit_length() - self.modulo.bit_length()
            if shift < 0:
                break
            x ^= self.modulo << shift
        return x

    def div(self, x, y):
        result = 0
        while True:
            shift = x.bit_length() - y.bit_length()
            if shift < 0:
                break
            x ^= y << shift
            result |= 1 << shift
        return result

    def eq(self, x, y):
        return self.sub(x, y) == 0

    def order(self):
        return 1 << (self.modulo.bit_length() - 1)

    def mul(self, x, y):
        result = 0
        for i in range(x.bit_length()):
            result ^= y * (x & (1 << i))
        return result

    def unit(self):
        return 1

    def inv(self, x):
        gcd, x, _ = self.gcd(x, self.modulo)
        assert gcd == 1
        return x
