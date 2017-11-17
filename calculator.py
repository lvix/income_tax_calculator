#!/usr/bin/env python3 

import sys

# constants
tax_threshold = 3500
tax_rate = [0.03, 0.10, 0.20, 0.25, 0.30, 0.35, 0.45]
fixed_value = [0, 105, 555, 1005, 2755, 5505, 13505]
tax_range = [0, 1500, 4500, 9000, 35000, 55000, 80000]
insure_rates = {
    'pension': 0.08,
    'medic': 0.02,
    'unemploy': 0.005,
    'workinj': 0,
    'reprod': 0,
    'accfunds': 0.06
}


def cal_insure_amount(salary):
    global insure_rates
    insure_sum = 0
    for k, v in insure_rates.items():
        insure_sum += salary * v
    return insure_sum


def cal_income_tax(salary):
    # calculate insurance amount
    insurance = cal_insure_amount(salary)
    # figure out the amount that should be taxed
    tax_amount = salary - insurance - tax_threshold
    if tax_amount > tax_range[-1]:
        level = 6
    else:
        for level in range(7):
            if tax_range[level] <= tax_amount < tax_range[level + 1]:
                break

    # figure out the final tax amount 
    tax_result = tax_amount * tax_rate[level] - fixed_value[level]

    if tax_result < 0:
        tax_result = 0
    return tax_result


def print_paycheck(emp_list):
    for emp in emp_list:
        emp_num = emp[0]
        emp_salary = emp[1]

        emp_income = emp_salary - cal_insure_amount(emp_salary) - cal_income_tax(emp_salary)
        print(str(emp_num) + ':' + format(emp_income, ".2f"))


def format_input(argv):
    if len(argv) < 2:
        print('Parameter Error')
        exit(0)
    else:
        arg_list = argv[1:]
        tmp_list = []
        for arg in arg_list:
            tmp_list.append(arg.split(':'))

        emp_list = []
        try:
            for t in tmp_list:
                emp_list.append([int(t[0]), int(t[1])])
        except:
            print('Parameter Error')
            exit(0)
        return emp_list


def main(argv):
    employees = format_input(argv)
    print_paycheck(employees)


if __name__ == '__main__':
    main(sys.argv)
    exit(0)
