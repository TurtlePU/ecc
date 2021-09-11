import sys
import traceback
from typing import Generic, List, Optional, Tuple, TypeVar
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


class Encoder(Generic[T]):
    def encode(self, text: str) -> List[T]:
        raise NotImplementedError

    def decode(self, code: List[T]) -> str:
        raise NotImplementedError


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
        return self.primary.decode([x for x in lst for lst in aligned])


def align(lst, length):
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


def ints(line: str):
    return map(int, line.split(' '))


def pair(a, b):
    return a, b


inf = open(sys.argv[1], 'r')

p, g, s = ints(inf.readline())
group = Zn(p)
k = group.pow(g, s)
text = inf.readline().rstrip('\n')

print(p, g, k)
print(text)
sys.stdout.close()

try:
    cipher = [pair(*ints(line)) for line in sys.stdin.readlines()]
except Exception:
    sys.exit(2)

try:
    deciphered = ElGamal(group, g, BaseEncoder(p)).decrypt(s, cipher)
    assert deciphered == text
except Exception:
    sys.stderr.write("'{}'\n'{}'\n".format(text.replace('\n', '    '), deciphered.replace('\n', '    ')))
    sys.exit(1)

open(sys.argv[2], 'w').write('ok\n')
