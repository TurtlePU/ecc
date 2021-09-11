import sys

def decrypt(c1, c2):
    return c2 * pow(c1, -k, p) % p

def decode(ms):
    num = 0
    for m in reversed(ms):
        num = num * p + m
    res = ''
    while num != 0:
        res += dec_char(num % 64)
        num //= 64
    return res

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

p, k = map(int, input().split(' '))
print(decode([decrypt(*map(int, line.split(' ')))
      for line in sys.stdin.readlines()]))
