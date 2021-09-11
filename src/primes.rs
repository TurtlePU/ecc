use std::collections::HashSet;

use rand::{prelude::IteratorRandom, thread_rng, Rng};
use rayon::iter::{IntoParallelIterator, ParallelIterator};

pub struct PrimeEncryption {
    pub safe_prime: u32,
    pub generator: u32,
}

pub fn prime_encryptions(
    rng: &mut impl Rng,
    from: u32,
    to: u32,
    limit: usize,
) -> impl ParallelIterator<Item = PrimeEncryption> {
    (from..to)
        .choose_multiple(rng, limit)
        .into_par_iter()
        .filter(|&n| is_safe_prime(n))
        .map(move |safe_prime| {
            let generator = generators_for_prime(safe_prime)
                .choose(&mut thread_rng())
                .unwrap();
            PrimeEncryption {
                safe_prime,
                generator,
            }
        })
}

pub fn generators_for_prime(safe_prime: u32) -> impl Iterator<Item = u32> {
    let safe_prime = safe_prime as u64;
    (2..safe_prime - 1).map(move |sqrt| (sqrt * sqrt % safe_prime) as u32)
}

pub fn is_prime(number: u128) -> bool {
    (number > 1)
        && (2..=sqrt(number))
            .into_par_iter()
            .all(|divisor| number % divisor != 0)
}

pub fn is_safe_prime(number: u32) -> bool {
    let number = number as u128;
    is_prime(number) && is_prime((number - 1) / 2)
}

fn sqrt(number: u128) -> u128 {
    (number as f64).sqrt() as u128
}

pub fn factorization(of: u128) -> Factorization {
    Factorization(of, 2)
}

pub struct Factorization(u128, u128);

impl Iterator for Factorization {
    type Item = u128;

    fn next(&mut self) -> Option<Self::Item> {
        if self.0 < self.1 * self.1 {
            None
        } else if self.0 % self.1 == 0 {
            self.0 /= self.1;
            Some(self.1)
        } else {
            self.1 += 1;
            self.next()
        }
    }
}

#[allow(unused)]
pub fn sieve(n: usize) -> HashSet<usize> {
    let mut least_primes = vec![0; n];
    let mut primes = vec![];
    for i in 2..n {
        if least_primes[i] == 0 {
            least_primes[i] = i;
            primes.push(i);
        }
        for &prime in &primes {
            if prime > least_primes[i] || i * prime > n {
                break;
            }
            least_primes[i * prime] = prime;
        }
    }
    primes.into_iter().collect()
}
