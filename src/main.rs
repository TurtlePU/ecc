use std::env::args;

use itertools::Itertools;
use polynomials::Poly;
use primes::{prime_encryptions, PrimeEncryption};
use rand::{prelude::ThreadRng, thread_rng};
use rayon::{iter::ParallelIterator, ThreadPoolBuilder};

use crate::{
    elliptic_curves::{create_curve_for, Curve},
    polynomials::{
        create_polynomial_encryption, is_good_prime, PolynomialEncryption,
    },
    primes::is_prime,
};

mod conversion;
mod elliptic_curves;
mod polynomials;
mod primes;

pub fn run_until<T: Send + Sync>(
    gen: impl Fn(&mut ThreadRng) -> Option<T> + Send + Sync,
    tries: usize,
) -> Option<T> {
    let rng = &mut thread_rng();
    for _ in 0..tries {
        if let Some(result) = gen(rng) {
            return Some(result);
        }
    }
    None
}

fn main() {
    ThreadPoolBuilder::new()
        .num_threads(16)
        .build_global()
        .unwrap();
    let mut args = args();
    args.next();
    println!("primes (P), polynomials (F) or elliptic (E)?");
    match &args.next().unwrap()[..] {
        "P" => main_primes(args),
        "F" => main_poly(args),
        "E" => main_ell(args),
        _ => unreachable!(),
    }
}

fn read_nums(args: impl Iterator<Item = String>) -> Vec<u32> {
    args.map(|x| x.parse().unwrap()).collect()
}

fn main_primes(args: impl Iterator<Item = String>) {
    println!("Primes. Input: 'from to limit'");
    let nums = read_nums(args);
    for PrimeEncryption {
        safe_prime,
        generator,
    } in
        prime_encryptions(&mut thread_rng(), nums[0], nums[1], nums[2] as usize)
            .collect::<Vec<_>>()
    {
        println!("{} {}", safe_prime, generator);
    }
}

fn main_poly(args: impl Iterator<Item = String>) {
    println!("Polynomials. Input: 'from to tries'");
    let nums = read_nums(args);
    for good_prime in nums[0]..nums[1] {
        if is_good_prime(good_prime) {
            if let Some(PolynomialEncryption {
                good_prime,
                irreducible,
                generator,
            }) = create_polynomial_encryption(good_prime, nums[2] as usize)
            {
                println!(
                    "{}\n{}\n{}\n",
                    good_prime,
                    spaced(irreducible),
                    spaced(generator)
                );
            }
        }
    }
}

fn spaced(poly: Poly) -> String {
    poly.coefs().into_iter().map(|x| x.to_string()).join(" ")
}

fn main_ell(args: impl Iterator<Item = String>) {
    println!("Elliptic curves. Input: 'from to deg tries'");
    let nums = read_nums(args);
    for prime in nums[0]..nums[1] {
        if is_prime(prime as u128) {
            if let Some(Curve {
                prime,
                irreducible,
                a,
                b,
                size,
            }) = create_curve_for(prime, nums[2] as usize, nums[3] as usize)
            {
                println!(
                    "{}\n{}\n{}\n{}\n{}\n",
                    prime,
                    spaced(irreducible),
                    spaced(a),
                    spaced(b),
                    size
                );
            }
        }
    }
}
