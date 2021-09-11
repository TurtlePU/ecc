import random
import sys


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


def ints(line: str):
    return map(int, line.split(' '))


params = [list(ints(line)) for line in sys.stdin.readlines()]
prefix = sys.argv[1]

for i in range(33):
    p, g = random.choice(params)
    s = random.randrange(1, (p - 1) // 2)
    text = ''.join(dec_char(random.randrange(0, 64))
                   for _ in range(random.randrange(1, 5000)))
    with open('{}_{}'.format(prefix, i), 'w') as f:
        f.write('{} {} {}\n{}'.format(p, g, s, text))
