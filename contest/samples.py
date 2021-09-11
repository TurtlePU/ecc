from gamal import ElGamal
from elliptic_curve import SolvableCurve, E, Point, PointEncoder
from prime_fields import Zn
from encoders import ChunkEncoder, ListEncoder
from polynomial import Fp
from typing import List
from bitsize import BinaryPoly


def elliptic_el_gamal(group: E, generator: Point) -> ElGamal[Point]:
    field_order = group.curve.field.order()
    rand_shift = _rand_shift_from_field_order(field_order)
    chunk_length = _chunk_length_from_field_order(field_order)
    encoder = PointEncoder(ChunkEncoder(chunk_length), group.curve, rand_shift)
    return ElGamal(group, generator, encoder)


def _chunk_length_from_field_order(field_order: int) -> int:
    return (field_order.bit_length() // 2) // 8


def _rand_shift_from_field_order(field_order: int) -> int:
    return (field_order.bit_length() - 1) // 2 + 1


def prime_field_el_gamal(group: Zn, generator: int) -> ElGamal[int]:
    chunk_length = _chunk_length_from_group_order(group.order())
    return ElGamal(group, generator, ChunkEncoder(chunk_length))


def _chunk_length_from_group_order(group_order: int) -> int:
    return group_order.bit_length() // 8


def polynomial_el_gamal(group: Fp, generator: List[int]) -> ElGamal[List[int]]:
    chunk_length = _chunk_length_from_group_order(group.over.order())
    primary = ChunkEncoder(chunk_length)
    list_length = _list_length_from_modulo_len(len(group.modulo))
    return ElGamal(group, generator, ListEncoder(primary, list_length))


def _list_length_from_modulo_len(ln: int) -> int:
    return ln - 1


def binary_el_gamal(group: BinaryPoly, generator: int) -> ElGamal[int]:
    chunk_length = _chunk_length_from_binary_modulo(group.modulo)
    return ElGamal(group, generator, ChunkEncoder(chunk_length))


def _chunk_length_from_binary_modulo(modulo: int) -> int:
    return (modulo.bit_length() - 1) // 8
