from typing import List, TypeVar
from algebra_base import Field, GcdMixin

T = TypeVar('T')


class Fp(GcdMixin[List[T]]):
    def __init__(self, over: Field[T], modulo: List[T]):
        self.over = over
        self.modulo = modulo

    def order(self):
        return self.over.order() ** (len(self.modulo) - 1)

    def into(self, x):
        return self.trim([self.over.into(x) for x in x])

    def eq(self, x, y):
        return self.is_zero(self.trim(self.sub(x, y)))

    def mul(self, x, y):
        z = [self.over.zero()] * (len(x) + len(y) - 1)
        for i, x in enumerate(x):
            for j, y in enumerate(y):
                z[i + j] = self.over.add(z[i + j], self.over.mul(x, y))
        return self._mod(x)

    def unit(self):
        return [self.over.unit()]

    def inv(self, x):
        gcd, x, _ = self.gcd(x, self.modulo)
        assert len(gcd) == 1
        k = self.over.inv(gcd[0])
        return self.trim([self.over.mul(x, k) for x in x])

    def add(self, x, y):
        x += [self.over.zero()] * (len(y) - len(x))
        y += [self.over.zero()] * (len(x) - len(y))
        return self.trim([self.over.add(x, y) for x, y in zip(x, y)])

    def zero(self):
        return []

    def is_zero(self, x):
        return len(x) == 0

    def neg(self, x):
        return self.trim([self.over.neg(x) for x in x])

    def _mod(self, x: List[T]) -> List[T]:
        if len(x) < len(self.modulo):
            return x
        mk = self.over.inv(self.modulo[-1])
        for i in range(len(x), len(self.modulo) - 1, -1):
            k = self.over.mul(x[i], mk)
            for j in range(len(self.modulo)):
                x[i - j] = self.over.sub(x[i - j],
                                         self.over.mul(self.modulo[-j], k))
        return self.trim(x)

    def div(self, x, y):
        if len(x) < len(y):
            return []
        mk = self.over.inv(y[-1])
        res = []
        for i in range(len(x), len(y) - 1, -1):
            k = self.over.mul(x[i], mk)
            for j in range(len(y)):
                x[i - j] = self.over.sub(x[i - j], self.over.mul(y[-j], k))
            res.append(k)
        res.reverse()
        return self.trim(res)

    def trim(self, x: List[T]) -> List[T]:
        while self.over.is_zero(x[-1]):
            x.pop()
        return x
