from sys import stdin, argv
from random import choice, randrange

primes = [int(line.split(' ')[0]) for line in stdin.readlines()]

for i in range(33):
    with open('{}_{}'.format(argv[1], i), 'w') as f:
        p = choice(primes)
        k = randrange(1, (p - 1) // 2)
        f.write('{} {}\n'.format(p, k))
        for _ in range(randrange(1, 1000)):
            c1 = randrange(1, p)
            c2 = randrange(1, p)
            f.write('{} {}\n'.format(c1, c2))
