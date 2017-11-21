#!/usr/bin/env python3

from random import randint
try:
    with open('user.csv', 'w') as f:
        for i in range(20):
            f.write('{},{}\n'.format(i, randint(3000, 7000)))
except:
    print('generation failed')
    exit(1)
