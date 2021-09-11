from dataclasses import dataclass
from typing import Generic, List, TypeVar

T = TypeVar('T')


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
        aligned = [ align(lst, self.list_length) for lst in code ]
        return self.primary.decode([ x for x in lst for lst in aligned ])


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


class Base64:
    def encode(self, text):
        bigint = 0
        for c in reversed(text):
            bigint = bigint * 64 + enc_char(c)
        return bigint

    def decode(self, code):
        result = ''
        while code != 0:
            result += dec_char(code % 64)
            code //= 64
        return result


@dataclass
class BaseEncoder(Encoder[int]):
    base: int
    digit: Base64

    def encode(self, text):
        bigint = self.digit.encode(text)
        result = []
        while bigint != 0:
            result.append(bigint % self.base)
            bigint //= self.base
        return result

    def decode(self, code):
        bigint = 0
        for c in reversed(code):
            bigint = bigint * self.base + c
        return self.digit.decode(bigint)


@dataclass
class LineEncoder(Encoder[int]):
    digit: Base64

    def encode(self, text):
        return [ self.digit.encode(line) for line in text.split('\n') ]

    def decode(self, code):
        return '\n'.join(self.digit.decode(c) for c in code)
