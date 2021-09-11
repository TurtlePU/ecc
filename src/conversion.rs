use std::{
    convert::TryInto,
    ops::{Add, DivAssign, Mul, Rem},
};

use num_bigint::BigInt;
use num_traits::Zero;

pub const ALPHABET_SIZE: usize = 64;

pub fn encode_ascii(symbol: u8) -> u8 {
    match symbol {
        32 => 62,
        46 => 63,
        48..=57 => symbol - 48,
        65..=90 => symbol - 55,
        97..=122 => symbol - 61,
        _ => unreachable!(),
    }
}

pub fn decode_ascii(number: u8) -> u8 {
    match number {
        0..=9 => 48 + number,
        10..=35 => 55 + number,
        36..=61 => 61 + number,
        62 => 32,
        63 => 46,
        _ => unreachable!(),
    }
}

#[allow(unused)]
pub fn encode_string(string: String) -> BigInt {
    unsequence::<_, BigInt, u8, usize>(
        string.into_bytes().into_iter().map(encode_ascii),
        ALPHABET_SIZE,
    )
}

#[allow(unused)]
pub fn decode_string(number: BigInt) -> String {
    String::from_utf8(
        sequence::<BigInt, BigInt, _>(number, ALPHABET_SIZE)
            .into_iter()
            .map(|digit| decode_ascii(digit.try_into().unwrap()))
            .collect(),
    )
    .unwrap()
}

pub fn sequence<T, U, M>(mut number: T, modulo: M) -> Vec<U>
where
    M: Copy,
    for<'a> &'a T: Rem<M, Output = U>,
    T: Zero + DivAssign<M>,
{
    let mut result = vec![];
    while !number.is_zero() {
        result.push(&number % modulo);
        number /= modulo;
    }
    result
}

pub fn unsequence<I, Z, U, T>(digits: I, modulo: T) -> Z
where
    I: DoubleEndedIterator<Item = U>,
    T: Copy,
    Z: Zero + Mul<T, Output = Z> + Add<U, Output = Z>,
{
    digits
        .into_iter()
        .rfold(Z::zero(), |result, digit| result * modulo + digit)
}
