#!/usr/bin/env python3

from random import randint
try:
    with open('user.csv', 'w') as f:
        for i in range(10):
            f.write('{},{}\n'.format(i, randint(3000, 8000)))
except:
    print('generation failed')
    exit(1)
