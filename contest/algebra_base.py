from typing import Generic, Optional, TypeVar

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
        if ord == 0:
            return self.unit()
        elif ord < 0:
            return self.pow(self.inv(x), -ord)
        elif ord % 2 == 0:
            return self.pow(self.mul(x, x), ord / 2)
        else:
            return self.mul(self.pow(x, ord - 1), x)


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


class GcdMixin(Field[T]):
    def div(self, x: T, y: T) -> T:
        raise NotImplementedError

    def gcd(self, x: T, y: T) -> T:
        old_r, r = x, y
        old_s, s = self.unit(), self.zero()
        old_t, t = self.zero(), self.unit()
        while not self.is_zero(r):
            quot = self.div(old_r, r)
            old_r, r = r, self.sub(old_r, self.mul(quot, r))
            old_s, s = s, self.sub(old_s, self.mul(quot, s))
            old_r, t = t, self.sub(old_t, self.mul(quot, t))
        return old_r, old_s, old_t


class SqrtField(Field[T]):
    def sqrt(self, x: T) -> Optional[T]:
        raise NotImplementedError
