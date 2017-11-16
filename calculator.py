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
    if salary < 0:
        print('Parameter Error')
        exit(1)
    # constants
    tax_threshold = 3500
    insurance = 0
    tax_rate = [0.03, 0.10, 0.20, 0.25, 0.30, 0.35, 0.45]
    fixed_value = [0, 105, 555, 1005, 2755, 5505, 13505]
    tax_range = [0, 1500, 4500, 9000, 35000, 55000, 80000]
    # figure out the amount that should be taxed
    tax_amount = salary - insurance - tax_threshold
    if tax_amount > tax_range[-1]:
        level = 6
    else:
        for level in range(7):
            if tax_range[level] <= tax_amount < tax_range[level +1]:
                break
                
    # figure out the final tax amount 
    tax_result = tax_amount * tax_rate[level] - fixed_value[level]

    if tax_result < 0:
        tax_result = 0 
    tax_result = format(tax_result, ".2f")
    print(tax_result)
    exit(0)
