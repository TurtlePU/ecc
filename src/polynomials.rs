use std::{
    fmt::{Debug, Display},
    ops::{AddAssign, Mul, Rem, SubAssign},
};

use num_bigint::BigInt;
use num_traits::{One, Zero};
use polynomial_ring::Polynomial;
use rand::{prelude::IteratorRandom, Rng};
use rayon::iter::*;
use ring_algorithm::modulo_inverse;

use crate::{primes::is_prime, run_until};

pub struct PolynomialEncryption {
    pub good_prime: u32,
    pub irreducible: Poly,
    pub generator: Poly,
}

#[allow(unused)]
pub fn polynomial_encryptions(
    rng: &mut impl Rng,
    from: u32,
    to: u32,
    limit: usize,
) -> impl ParallelIterator<Item = PolynomialEncryption> {
    (from..to)
        .choose_multiple(rng, limit)
        .into_par_iter()
        .filter(|&num| is_good_prime(num))
        .filter_map(|good_prime| create_polynomial_encryption(good_prime, 100))
}

pub fn create_polynomial_encryption(
    good_prime: u32,
    tries: usize,
) -> Option<PolynomialEncryption> {
    let irreducible = find_irreducible(good_prime, 3, tries)?;
    let generator = run_until(
        |rng| {
            let source = sample_poly(rng, good_prime, 3);
            maybe_generator(good_prime, &irreducible, source)
        },
        tries,
    )
    .unwrap();
    PolynomialEncryption {
        good_prime,
        irreducible,
        generator,
    }
    .into()
}

pub fn find_irreducible(
    good_prime: u32,
    deg: usize,
    tries: usize,
) -> Option<Poly> {
    run_until(
        |rng| {
            let poly = sample_poly(rng, good_prime, deg);
            if is_irreducible::<Num, _>(poly.clone(), &good_prime) {
                Some(poly)
            } else {
                None
            }
        },
        tries,
    )
}

pub fn is_good_prime(number: u32) -> bool {
    let number = number as u128;
    is_prime(number) && is_prime((number.pow(3) - 1) / (number - 1))
}

pub type Num = BigInt;
pub type Poly<T = Num> = Polynomial<T>;
pub type Mat<T = Num> = Vec<Vec<T>>;

pub fn sample_poly(rng: &mut impl Rng, prime: u32, deg: usize) -> Poly {
    let mut coefs = vec![1u32; deg + 1];
    rng.fill(&mut coefs[..deg]);
    Poly::new(coefs.into_iter().map(|x| BigInt::from(x % prime)).collect())
}

pub fn maybe_generator(
    good_prime: u32,
    irreducible: &Poly,
    source: Poly,
) -> Option<Poly> {
    let generator = power(source, good_prime - 1, irreducible, good_prime);
    if is_constant(generator.clone(), &good_prime) {
        None
    } else {
        Some(generator)
    }
}

fn power(mut x: Poly, mut pow: u32, m: &Poly, p: u32) -> Poly {
    let mut y = Poly::<Num>::one();
    while pow > 0 {
        if pow % 2 == 0 {
            x = trim(&x * &x % m, p);
            pow /= 2;
        } else {
            y = trim(y * &x % m, p);
            pow -= 1;
        }
    }
    y
}

pub fn trim(poly: Poly, prime: u32) -> Poly {
    Poly::new(poly.coefs().into_iter().map(|x| x % prime).collect())
}

pub trait FieldChar<T = Num>: Send + Sync {
    fn is_zero(&self, elem: &T) -> bool;

    fn order(&self) -> usize;

    fn inverse(&self, elem: T) -> T;

    fn intern(&self, poly: Poly<T>) -> Poly<T>;
}

impl FieldChar for u32 {
    fn is_zero(&self, x: &Num) -> bool {
        (x % self).is_zero()
    }

    fn order(&self) -> usize {
        *self as usize
    }

    fn inverse(&self, elem: Num) -> Num {
        modulo_inverse::<Num>(elem, (*self).into()).unwrap()
    }

    fn intern(&self, poly: Poly) -> Poly {
        trim(poly, *self)
    }
}

pub fn is_irreducible<T, F>(f: Poly<T>, p: &F) -> bool
where
    T: for<'a> AddAssign<&'a T>
        + SubAssign
        + One
        + Zero
        + Eq
        + Clone
        + Debug
        + Display
        + Send
        + Sync,
    for<'a> &'a T: Mul<&'a T, Output = T>,
    for<'a> &'a Poly<T>: Mul<&'a T, Output = Poly<T>>,
    Poly<T>: for<'a> Rem<&'a Poly<T>, Output = Poly<T>>
        + Rem<Output = Poly<T>>
        + Zero
        + Clone,
    F: FieldChar<T>,
{
    if is_constant::<T, F>(f.clone(), p) {
        return false;
    }
    let div = gcd::<T, F>(f.clone(), f.clone().derivative(), p);
    if !is_constant::<T, F>(div, p) {
        return false;
    }
    kerdim::<T, F>(operator::<T, F>(&f, p), p) == 1
}

fn gcd<T, F>(mut a: Poly<T>, mut b: Poly<T>, p: &F) -> Poly<T>
where
    for<'a> &'a Poly<T>: Mul<&'a T, Output = Poly<T>>,
    Poly<T>: Rem<Output = Poly<T>> + Zero + Clone,
    T: One + Clone,
    F: FieldChar<T>,
{
    a = p.intern(a);
    b = p.intern(b);
    while !b.is_zero() {
        let ref k = normalize(&mut a, &mut b, p);
        a = &replace::<T>(p.intern(a % b.clone()), &mut b) * k;
        b = &b * k;
    }
    return a;

    fn replace<T>(x: Poly<T>, y: &mut Poly<T>) -> Poly<T> {
        std::mem::replace(y, x)
    }

    fn normalize<T, F>(x: &mut Poly<T>, y: &mut Poly<T>, p: &F) -> T
    where
        for<'a> &'a Poly<T>: Mul<&'a T, Output = Poly<T>>,
        T: One + Clone,
        F: FieldChar<T>,
    {
        let w = y.lc().cloned().unwrap_or_else(T::one);
        let ref z = p.inverse(w.clone());
        *x = p.intern(&*x * z);
        *y = p.intern(&*y * z);
        w
    }
}

fn is_constant<T, F>(poly: Poly<T>, p: &F) -> bool
where
    T: Send + Sync,
    F: FieldChar<T>,
{
    poly.coefs()
        .into_iter()
        .skip(1)
        .all(move |coef| p.is_zero(&coef))
}

fn operator<T, F>(f: &Poly<T>, p: &F) -> Mat<T>
where
    T: SubAssign + One + Zero + Clone + Debug + Send + Sync,
    Poly<T>: for<'a> Rem<&'a Poly<T>, Output = Poly<T>>,
    F: FieldChar<T>,
{
    let n = f.deg().unwrap_or_default();
    (0..n)
        .map(|deg| operator_row::<T, F>(f, p, deg as u32))
        .collect()
}

fn operator_row<T, F>(f: &Poly<T>, p: &F, deg: u32) -> Vec<T>
where
    T: SubAssign + One + Zero + Clone + Debug,
    Poly<T>: for<'a> Rem<&'a Poly<T>, Output = Poly<T>>,
    F: FieldChar<T>,
{
    let pow = p.order() * deg as usize;
    let poly = Poly::from_monomial(T::one(), pow);
    let factored = p.intern(poly % f);
    let mut coefs = factored.coefs();
    let n = f.deg().unwrap_or_default();
    if coefs.len() < n {
        coefs.resize(n, T::zero());
    }
    coefs[deg as usize] -= T::one();
    coefs
}

fn kerdim<T, F>(mat: Mat<T>, p: &F) -> usize
where
    T: SubAssign + Clone + Debug + Send + Sync,
    for<'a> &'a T: Mul<&'a T, Output = T>,
    F: FieldChar<T>,
{
    return kerdim_impl::<T, F>(mat, p, 0);

    fn kerdim_impl<T, F>(mut mat: Mat<T>, p: &F, ans: usize) -> usize
    where
        T: SubAssign + Clone + Debug + Send + Sync,
        for<'a> &'a T: Mul<&'a T, Output = T>,
        F: FieldChar<T>,
    {
        let rank_row_impl = |mut mat: Mat<T>, row: Vec<T>, pivot: usize| {
            let inv = p.inverse(row[pivot].clone());
            mat.par_iter_mut().for_each(|rowj| {
                let coeff = &rowj[pivot] * &inv;
                rowj.par_iter_mut().zip(&row).for_each(|(elem, ilem)| {
                    *elem -= &coeff * ilem;
                });
            });
            kerdim_impl::<T, F>(mat, p, ans)
        };
        match mat.pop() {
            Some(row) => {
                let pivot = row.par_iter().position_any(|x| !p.is_zero(x));
                match pivot {
                    Some(pivot) => rank_row_impl(mat, row, pivot),
                    None => kerdim_impl::<T, F>(mat, p, ans + 1),
                }
            }
            None => ans,
        }
    }
}
