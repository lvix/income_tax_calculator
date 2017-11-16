#!/usr/bin/env python3 

import sys 

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Parameter Error')
        exit(1)
    try:
        salary = int(sys.argv[1])
    except:
        print('Parameter Error')
        exit(1)
    
    # constants
    tax_threshold = 3500
    insurance = 0
    tax_rate = [0.03, 0.10, 0.20, 0.25, 0.30, 0.35, 0.45]
    fixed_value = [0, 105, 555, 1005, 2755, 5505, 13505]

    # figure out the amount that should be taxed
    tax_amount = salary - insurance - tax_threshold

    if tax_amount <= 1500:
        level = 0
    elif 1500 <= tax_amount < 4500:
        level = 1
    elif 4500 <= tax_amount < 9000:
        level = 2
    elif 9000 <= tax_amount < 35000:
        level = 3
    elif 35000 <= tax_amount < 55000:
        level = 4
    elif 55000 <= tax_amount < 80000:
        level = 5
    elif 80000 <= tax_amount:
        level = 6

    # figure out the final tax amount 
    tax_result = tax_amount * tax_rate[level] - fixed_value[level]

    if tax_result < 0:
        tax_result = 0 
    tax_result = format(tax_result, ".2f")
    print(tax_result)
    exit(0)
