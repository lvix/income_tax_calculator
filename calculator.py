#!/usr/bin/env python3 

import sys

# constants


insure_rates = {
    'pension': 0.08,
    'medic': 0.02,
    'unemploy': 0.005,
    'workinj': 0,
    'reprod': 0,
    'accfunds': 0.06
}


# classes
class Config(object):
    default_keys = ['JiShuL', 'JiShuH', 'YangLao', 'YiLiao', 'ShiYe', 'GongShang', 'ShengYu', 'GongJiJin']

    def __init__(self, file_path):
        self.rates = {}
        try:
            cfg = open(file_path)
            for l in cfg:
                line = l.split('=')
                self.rates[line[0].strip()] = float(line[1])
            cfg.close()
        except:
            self.__error()

        # print(self.rates.keys())
        for key in self.rates.keys():
            if key not in self.default_keys:
                self.__error()

        try:
            self.JiShuL = self.rates.pop('JiShuL')
            self.JiShuH = self.rates.pop('JiShuH')
        except:
            self.__error()
        if self.JiShuL > self.JiShuH:
            self.__error()
        # print(self.rates.keys)

    def cal_insure_amount(self, salary):
        insure_sum = 0
        if salary < self.JiShuL:
            cal_amount = self.JiShuL
        elif salary > self.JiShuH:
            cal_amount = self.JiShuH
        else:
            cal_amount = salary
        for k, v in self.rates.items():
            insure_sum += cal_amount * v
        return insure_sum

    @staticmethod
    def __error():
        print('Parameter Error')
        exit(1)


class UserData(object):
    tax_rate = [0.03, 0.10, 0.20, 0.25, 0.30, 0.35, 0.45]
    tax_threshold = 3500
    fixed_value = [0, 105, 555, 1005, 2755, 5505, 13505]
    tax_range = [0, 1500, 4500, 9000, 35000, 55000, 80000]

    def __init__(self, file_path, config):
        self.users = {}
        self.config = config
        try:
            with open(file_path) as f:
                for l in f:
                    line = l.split(',')
                    self.users[int(line[0])] = int(line[1])
        except:
            self.__error()
        # print(self.users)

    @staticmethod
    def __error():
        print('Parameter Error')
        exit(1)

    def cal_income_tax(self, salary):
        # calculate insurance amount
        insurance = self.config.cal_insure_amount(salary)
        # figure out the amount that should be taxed
        tax_amount = salary - insurance - self.tax_threshold
        if tax_amount > self.tax_range[-1]:
            level = 6
        else:
            for level in range(7):
                if self.tax_range[level] <= tax_amount < self.tax_range[level + 1]:
                    break

        # figure out the final tax amount
        tax_result = tax_amount * self.tax_rate[level] - self.fixed_value[level]

        if tax_result < 0:
            tax_result = 0
        return tax_result

    def gen_paycheck(self, dump_file):
        try:
            f = open(dump_file, 'w')
            for user_num, user_salary in self.users.items():
                user_insure = self.config.cal_insure_amount(user_salary)
                user_income_tax = self.cal_income_tax(user_salary)
                user_actual_income = user_salary - user_insure - user_income_tax
                # 工号,税前工资,社保金额,个税金额,税后工资
                user_info = '{0},{1},{2},{3},{4}'.format(str(user_num), str(user_salary), format(user_insure, ".2f"),
                                                         format(user_income_tax, ".2f"), format(user_actual_income, ".2f"))
                f.write('{}\n'.format(user_info))
            f.close()
        except:
            f.close()
            self.__error()


def main(argv):
    if len(argv) < 7:
        print('Parameter Error')
        exit(0)
    else:
        # ./calculator.py -c /home/shiyanlou/test.cfg -d /home/shiyanlou/user.csv -o /tmp/gongzi.csv
        arg_list = argv[1:]
        if arg_list[0] != '-c' or arg_list[2] != '-d' or arg_list[4] != '-o':
            print('Parameter Error')
            exit(0)

        cfg_file = arg_list[1]
        user_file = arg_list[3]
        output_file = arg_list[5]

        conf = Config(cfg_file)
        users = UserData(user_file, conf)
        users.gen_paycheck(output_file)


if __name__ == '__main__':
    main(sys.argv)
    # con = Config('test.cfg')
    # print(con.cal_insure_amount(4500))
    # users = UserData('user.csv', con)
    # users.gen_paycheck()
    exit(0)
