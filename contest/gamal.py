from typing import Generic, List, Tuple, TypeVar
from algebra_base import Group
from encoders import Encoder
from random import randrange

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
