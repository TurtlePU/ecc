use num_traits::{One, Zero};
use rand::{prelude::IteratorRandom, Rng};
use rayon::iter::{IntoParallelIterator, ParallelIterator};
use ring_algorithm::modulo_inverse;

use crate::{
    conversion::sequence,
    polynomials::{
        find_irreducible, is_irreducible, sample_poly, trim, FieldChar, Num,
        Poly,
    },
    primes::{factorization, is_prime},
    run_until,
};

pub struct Curve {
    pub prime: u32,
    pub irreducible: Poly,
    pub a: Poly,
    pub b: Poly,
    pub size: usize,
}

#[allow(unused)]
pub fn curves(
    rng: &mut impl Rng,
    from: u32,
    to: u32,
    limit: usize,
    tries: usize,
    deg: usize,
) -> impl ParallelIterator<Item = Curve> {
    (from..to)
        .choose_multiple(rng, limit)
        .into_par_iter()
        .filter(|&x| is_prime(x as u128))
        .filter_map(move |prime| create_curve_for(prime, deg, tries))
}

pub fn create_curve_for(prime: u32, deg: usize, tries: usize) -> Option<Curve> {
    let irreducible = find_irreducible(prime, deg, tries)?;
    run_until(
        |rng| {
            create_curve(
                prime,
                &irreducible,
                sample_poly_field(rng, prime, &irreducible),
                sample_poly_field(rng, prime, &irreducible),
            )
        },
        tries,
    )
}

pub fn create_curve(
    prime: u32,
    irreducible: &Poly,
    a: Poly,
    b: Poly,
) -> Option<Curve> {
    if check_curve(prime, irreducible, &a, &b) {
        let size = count_size(prime, irreducible, &a, &b);
        if good_enough(size as u128) {
            let irreducible = irreducible.clone();
            Some(Curve {
                prime,
                irreducible,
                a,
                b,
                size,
            })
        } else {
            None
        }
    } else {
        None
    }
}

fn good_enough(size: u128) -> bool {
    let last_prime = factorization(size).last().unwrap();
    last_prime * last_prime >= size
}

pub fn count_size(prime: u32, irreducible: &Poly, a: &Poly, b: &Poly) -> usize {
    (0..(prime as u128).pow(irreducible.deg().unwrap() as u32))
        .map(|number| into_field(prime as u128, number))
        .filter(|x| is_solution(prime, irreducible, a, b, x))
        .count()
}

fn into_field(prime: u128, number: u128) -> Poly<Num> {
    let seq = sequence::<u128, u128, u128>(number, prime);
    Poly::new(seq.into_iter().map(Num::from).collect())
}

fn is_solution(
    prime: u32,
    irreducible: &Poly,
    a: &Poly,
    b: &Poly,
    x: &Poly,
) -> bool {
    is_square(prime, irreducible, x * x * x + a * x + b)
}

fn is_square(prime: u32, irreducible: &Poly, y: Poly) -> bool {
    is_irreducible::<Poly, _>(
        Poly::new(vec![-y, Zero::zero(), One::one()]),
        &FieldParams(prime, irreducible),
    )
}

struct FieldParams<'a>(u32, &'a Poly);

impl FieldChar<Poly> for FieldParams<'_> {
    fn is_zero(&self, elem: &Poly) -> bool {
        elem.clone()
            .coefs()
            .into_par_iter()
            .all(|x| FieldChar::is_zero(&self.0, &x))
    }

    fn order(&self) -> usize {
        (self.0 as usize).pow(self.1.deg().unwrap() as u32)
    }

    fn inverse(&self, elem: Poly) -> Poly {
        modulo_inverse::<Poly>(trim(elem % self.1, self.0), self.1.clone())
            .unwrap()
    }

    fn intern(&self, poly: Poly<Poly>) -> Poly<Poly> {
        Poly::<Poly>::new(
            poly.coefs()
                .into_iter()
                .map(|x| self.0.intern(x % self.1))
                .collect(),
        )
    }
}

pub fn check_curve(prime: u32, irreducible: &Poly, a: &Poly, b: &Poly) -> bool {
    ((a * a * a * Num::from(4) + b * b * Num::from(27)) % irreducible)
        .coefs()
        .into_iter()
        .any(|x| !(x % prime).is_zero())
}

pub fn sample_poly_field(
    rng: &mut impl Rng,
    prime: u32,
    irreducible: &Poly,
) -> Poly {
    sample_poly(rng, prime, irreducible.deg().unwrap()) % irreducible
}
