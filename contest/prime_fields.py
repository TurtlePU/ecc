from dataclasses import dataclass
from algebra_base import SqrtField

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
