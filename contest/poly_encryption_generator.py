import sys
from typing import Generic, List, Optional, Tuple, TypeVar
from random import randrange

T = TypeVar('T')


class Group(Generic[T]):
    def print(self, msg: str, x: T):
        raise NotImplementedError

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
            if ord % 2 == 0:
                x = self.mul(x, x)
                ord //= 2
            else:
                result = self.mul(result, x)
                ord -= 1
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


class GcdMixin(Field[T]):
    def div(self, x: T, y: T) -> T:
        raise NotImplementedError

    def gcd(self, x: T, y: T) -> T:
        old_r, r = x, y
        old_s, s = self.unit(), self.zero()
        old_t, t = self.zero(), self.unit()
        while not self.is_zero(r):
            quot = self.div(old_r, r)
            new_r = self.into(self.sub(old_r, self.mul(quot, r)))
            new_s = self.into(self.sub(old_s, self.mul(quot, s)))
            new_t = self.into(self.sub(old_t, self.mul(quot, t)))
            old_r, old_s, old_t = r, s, t
            r, s, t = new_r, new_s, new_t
        return old_r, old_s, old_t


class SqrtField(Field[T]):
    def sqrt(self, x: T) -> Optional[T]:
        raise NotImplementedError


class Fp(GcdMixin[List[T]]):
    def __init__(self, over: Field[T], modulo: List[T]):
        self.over = over
        self.modulo = modulo

    def print(self, msg, x):
        print(msg + ':', *x, file=sys.stderr)

    def order(self):
        return self.over.order() ** (len(self.modulo) - 1)

    def into(self, x):
        return self._mod([self.over.into(xx) for xx in x])

    def eq(self, x, y):
        return self.is_zero(self.trim(self.sub(x, y)))

    def mul(self, x, y):
        z = [self.over.zero()] * (len(x) + len(y) - 1)
        for i, xx in enumerate(x):
            for j, yy in enumerate(y):
                z[i + j] = self.over.add(z[i + j], self.over.mul(xx, yy))
        return self._mod(z)

    def unit(self):
        return [self.over.unit()]

    def inv(self, x):
        gcd, x, _ = self.gcd(x, self.modulo)
        assert len(gcd) == 1
        k = self.over.inv(gcd[0])
        return self.trim([self.over.mul(xx, k) for xx in x])

    def add(self, x, y):
        x = x + [self.over.zero()] * (len(y) - len(x))
        y = y + [self.over.zero()] * (len(x) - len(y))
        return self.trim([self.over.add(xx, yy) for xx, yy in zip(x, y)])

    def zero(self):
        return []

    def is_zero(self, x):
        return len(self.trim(x)) == 0

    def neg(self, x):
        return self.trim([self.over.neg(xx) for xx in x])

    def _mod(self, x: List[T]) -> List[T]:
        if len(x) < len(self.modulo):
            return x
        mk = self.over.inv(self.modulo[-1])
        x = [ xx for xx in x ]
        for i in reversed(range(len(self.modulo) - 1, len(x))):
            k = self.over.mul(x[i], mk)
            for j in range(len(self.modulo)):
                x[i - j] = self.over.sub(x[i - j],
                                         self.over.mul(self.modulo[-j - 1], k))
        return self.trim(x)

    def div(self, x, y):
        if len(x) < len(y):
            return []
        mk = self.over.inv(y[-1])
        res = []
        x = [ xx for xx in x ]
        for i in reversed(range(len(y) - 1, len(x))):
            k = self.over.mul(x[i], mk)
            for j in range(len(y)):
                x[i - j] = self.over.sub(x[i - j], self.over.mul(y[-j - 1], k))
            res.append(k)
        res.reverse()
        return self.trim(res)

    def trim(self, x: List[T]) -> List[T]:
        x = [ xx for xx in x ]
        while len(x) > 0 and self.over.is_zero(x[-1]):
            x.pop()
        return x


class Encoder(Generic[T]):
    def encode(self, text: str) -> List[T]:
        raise NotImplementedError

    def decode(self, code: List[T]) -> str:
        raise NotImplementedError


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


class ChunkEncoder(Encoder[int]):
    def __init__(self, chunk_length: int):
        self.chunk_length = chunk_length

    def encode(self, text):
        ch = chunks(bytearray(text, 'utf-8'), self.chunk_length)
        return [int.from_bytes(c, 'little') for c in ch]

    def decode(self, code):
        bits = (c.to_bytes(self.chunk_length, 'little') for c in code)
        return bytearray().join(bits)


def chunks(it, n):
    for i in range(0, len(it), n):
        yield it[i:i+n]


class ListEncoder(Encoder[List[int]]):
    def __init__(self, primary: Encoder[int], list_length: int):
        self.primary = primary
        self.list_length = list_length

    def encode(self, text):
        return list(chunks(self.primary.encode(text), self.list_length))

    def decode(self, code):
        aligned = [align(lst, self.list_length) for lst in code]
        return self.primary.decode([x for lst in aligned for x in lst])


def align(lst, length):
    assert len(lst) <= length
    return lst + [0] * (length - len(lst))


def dec_char(number):
    if 0 <= number <= 9:
        return chr(48 + number)
    if 10 <= number <= 35:
        return chr(55 + number)
    if 36 <= number <= 61:
        return chr(61 + number)
    if number == 62:
        return ' '
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
    if symbol == 32:
        return 62
    if symbol == 46:
        return 63
    raise Exception()


class BaseEncoder(Encoder[int]):
    def __init__(self, base: int):
        self.base = base

    def encode(self, text):
        bigint = 0
        for c in reversed(text):
            bigint = bigint * 64 + enc_char(c)
        result = []
        while bigint != 0:
            result.append(bigint % self.base)
            bigint //= self.base
        return result

    def decode(self, code):
        bigint = 0
        for c in reversed(code):
            bigint = bigint * self.base + c
        result = ''
        while bigint != 0:
            result += dec_char(bigint % 64)
            bigint //= 64
        return result


class Zn(SqrtField[int]):
    def __init__(self, N: int):
        self.N = N

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
        return pow(x, -1, self.N)

    def pow(self, x, ord):
        return pow(x, ord, self.N)

    def add(self, x, y):
        return (x + y) % self.N

    def zero(self):
        return 0

    def neg(self, x):
        return self.N - x % self.N

    def sqrt(self, x):
        assert self.N % 4 == 3
        sqrt = x ** ((self.N + 1) / 4)
        if sqrt ** 2 == x:
            return sqrt
        else:
            return None


def read_poly(line: str):
    return list(map(int, line.split(' ')))


inputs = list(chunks(list(sys.stdin.readlines()), 4))

from random import randrange

for i, (p, f, g, _) in enumerate(inputs):
    p = int(p)
    f = read_poly(f)
    g = read_poly(g)
    s = randrange(1, (p ** 3 - 1) // (p - 1))
    text = ''.join(dec_char(randrange(64)) for _ in range(randrange(1, 1000)))
    with open('{}_{}'.format(sys.argv[1], i), 'w') as file:
        print(p, file=file)
        print(*f, file=file)
        print(*g, file=file)
        print(s, file=file)
        print(text, file=file)
