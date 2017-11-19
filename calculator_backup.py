#!/usr/bin/env python3 

import sys, os
from multiprocessing import Process, Value, Queue

# Multiprocessing
# 错误flag，置位后所有进程停止工作，退出程序
is_error = Value('i', 0)
#
is_reading_finished = Value('i', 0)
is_cal_finished = Value('i', 0)
is_writing_finished = Value('i', 0)
# 从用户信息中读取，即将计算个税的队列
q_user_data = Queue()

# 即将写入到文件的队列
q_output_data = Queue()


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

    @staticmethod
    def __error():
        print('Parameter Error')
        exit(1)

    def gen_simple_list(self):
        simple_list = [self.JiShuL, self.JiShuH]
        simple_list += self.rates
        return simple_list


def cal_insure_amount(config_list, salary):
    insure_sum = 0
    JiShuL = config_list[0]
    JiShuH = config_list[1]
    rates = config_list[2:]

    if salary < JiShuL:
        cal_amount = JiShuL
    elif salary > JiShuH:
        cal_amount = JiShuH
    else:
        cal_amount = salary
    for v in rates:
        insure_sum += cal_amount * v
    return insure_sum


class UserData(object):
    """
    按配置信息，计算员工的社保金额、个人所得税、实际收入等信息，
    并输出到指定的文件中
    """
    tax_rate = [0.03, 0.10, 0.20, 0.25, 0.30, 0.35, 0.45]
    tax_threshold = 3500
    fixed_value = [0, 105, 555, 1005, 2755, 5505, 13505]
    tax_range = [0, 1500, 4500, 9000, 35000, 55000, 80000]

    def __init__(self, config, data_file, dump_file):
        # self.users = {}
        self.config = config
        self.data_file = data_file
        self.dump_file = dump_file


    @staticmethod
    def __error():
        # print('Parameter Error')
        # exit(1)
        is_error.value = 1


def cal_income_tax(config_list, salary, user_data):
    # 计算社保金额
    insurance = cal_insure_amount(config_list, salary)
    # 计算应纳税金额
    tax_amount = salary - insurance - user_data.tax_threshold
    if tax_amount > user_data.tax_range[-1]:
        level = 6
    else:
        for level in range(7):
            if user_data.tax_range[level] <= tax_amount < user_data.tax_range[level + 1]:
                break

    # figure out the final tax amount
    tax_result = tax_amount * user_data.tax_rate[level] - user_data.fixed_value[level]

    if tax_result < 0:
        tax_result = 0
    return tax_result


def p_error():
    is_error.value = 1


def read_data(data_file):
    print('read process pid: {}'.format(os.getpid()))
    try:
        with open(data_file) as f:
            for l in f:
                if is_error.value == 1:
                    return
                line = l.split(',')
                q_user_data.put([int(line[0]), int(line[1])])
            is_reading_finished.value = 1
    except:
        # print('read error')
        p_error()
        return


def cal_data(config_list, user_data):
    print('cal process pid: {}'.format(os.getpid()))
    try:
        while is_error.value == 0 and not (is_reading_finished.value == 1 and q_user_data.empty()):
            if not q_user_data.empty():
                user_num, user_salary = q_user_data.get()
                user_insure = cal_insure_amount(config_list, user_salary)
                user_income_tax = cal_income_tax(config_list, user_salary, user_data)
                user_actual_income = user_salary - user_insure - user_income_tax
                output_list = [user_num, user_salary, user_insure, user_income_tax, user_actual_income]
                q_output_data.put(output_list)
        if is_error.value == 1:
            return
        is_cal_finished.value = 1
    except:
        # print('cal_error')
        p_error()
        return


def write_data(dump_file):
    print('write process pid: {}'.format(os.getpid()))
    try:
        f = open(dump_file, 'w')
        while is_error.value == 0 and not(is_reading_finished.value == 1 and is_cal_finished.value == 1 and q_output_data.empty()):
            if not q_output_data.empty():
                output_data = q_output_data.get()
                user_info = '{0},{1},{2},{3},{4}\n'.format(str(output_data[0]), str(output_data[1]), format(output_data[2], ".2f"),
                                                     format(output_data[3], ".2f"), format(output_data[4], ".2f"))
                f.write(user_info)
        if is_error.value == 1:
            f.close()
            return
    except:
        # print('write error')
        f.close()
        p_error()
        return


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
        users = UserData(conf, user_file, output_file)
        c_list = conf.gen_simple_list()

        p_read = Process(target=read_data, args=(user_file, ))
        p_cal = Process(target=cal_data, args=(c_list, users, ))
        p_write = Process(target=write_data, args=(output_file, ))

        p_read.start()
        p_cal.start()
        p_write.start()

        p_read.join()
        p_cal.join()
        p_write.join()

        if is_error.value == 1:
            print('Parameter Error')
            exit(1)


if __name__ == '__main__':
    main(sys.argv)
    # con = Config('test.cfg')
    # print(con.cal_insure_amount(4500))
    # users = UserData('user.csv', con)
    # users.gen_paycheck()
    exit(0)
