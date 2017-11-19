#!/usr/bin/env python3 

import sys, os
from multiprocessing import Process, Value, Queue, Lock
import time


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
        pass
        # print('Parameter Error')
        # exit(1)

    def cal_income_tax(self, salary):
        # 计算社保金额
        insurance = self.config.cal_insure_amount(salary)
        # 计算应纳税金额
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

    def read_data(self, is_error, cal_lock, user_q):
        # print('read:{}'.format(os.getpid()))
        try:
            with open(self.data_file) as f:
                for l in f:
                    if is_error.value == 1:
                        return
                    line = l.split(',')
                    with cal_lock:
                        user_q.put([int(line[0]), int(line[1])])
                with cal_lock:
                    user_q.put(['READ', 'FIN'])
        except:
            with cal_lock:
                is_error.value = 1
            return

    def cal_data(self, is_error, cal_lock, user_q, out_q):
        # print('cal:{}'.format(os.getpid()))
        try:
            while 1:

                if is_error.value == 1:
                    return
                if not user_q.empty():
                    with cal_lock:
                        user_num, user_salary = user_q.get()
                    if user_num == 'READ' and user_salary == 'FIN':
                        break
                    # print('cal gets: ', user_num, user_salary)
                    user_insure = self.config.cal_insure_amount(user_salary)
                    user_income_tax = self.cal_income_tax(user_salary)
                    user_actual_income = user_salary - user_insure - user_income_tax
                    output_list = [user_num, user_salary, user_insure, user_income_tax, user_actual_income]
                    with cal_lock:
                        out_q.put(output_list)
            with cal_lock:
                out_q.put(['CAL', 'FIN'])
                # is_cal_fin.value = 1
        except:
            with cal_lock:
                is_error.value = 1
            return

    def write_data(self, is_error, cal_lock, out_q):
        # print('write:{}'.format(os.getpid()))
        try:
            f = open(self.dump_file, 'w')
            while 1:

                if is_error.value == 1:
                    f.close()
                    return
                if not out_q.empty():
                    with cal_lock:
                        output_data = out_q.get()
                    if output_data[0] == 'CAL' and output_data[1] == 'FIN':
                        f.close()
                        break
                    user_info = '{0},{1},{2},{3},{4}\n'.format(str(output_data[0]),
                                                               str(output_data[1]),
                                                               format(output_data[2], ".2f"),
                                                               format(output_data[3], ".2f"),
                                                               format(output_data[4], ".2f"))
                    f.write(user_info)
        except:
            print('write error')
            f.close()
            with cal_lock:
                is_error.value = 1
            return


def main(argv):
    if len(argv) < 7:
        print('Parameter Error')
        exit(0)
    else:
        # ./calculator.py -c /home/shiyanlou/test.cfg -d /home/shiyanlou/user.csv -o /tmp/gongzi.csv

        arg_list = argv[1:]

        cfg_file = None
        user_file = None
        output_file = None

        for i in range(len(arg_list)):
            if arg_list[i] == '-c':
                cfg_file = arg_list[i + 1]
            elif arg_list[i] == '-d':
                user_file = arg_list[i + 1]
            elif arg_list[i] == '-o':
                output_file = arg_list[i + 1]

        if cfg_file is None or user_file is None or output_file is None:
            print('Parameter Error')
            exit(0)

        conf = Config(cfg_file)
        users = UserData(conf, user_file, output_file)

        # Multiprocessing
        # 错误flag，置位后所有进程停止工作，退出程序
        is_error = Value('i', 0)

        # 从用户信息中读取，即将计算个税的队列
        user_q = Queue()

        # 即将写入到文件的队列
        out_q = Queue()

        # Lock
        cal_lock = Lock()

        p_read = Process(target=users.read_data, args=(is_error, cal_lock, user_q,))
        p_cal = Process(target=users.cal_data, args=(is_error, cal_lock, user_q, out_q,))
        p_write = Process(target=users.write_data, args=(is_error, cal_lock, out_q,))

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
    exit(0)
