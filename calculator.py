#!/usr/bin/env python3 

import sys, os
import getopt
from multiprocessing import Process, Value, Queue, Lock
from datetime import datetime
import configparser


# classes
class Config(object):
    """
    根据Parser 生成对应的社保信息，
    并计算社保金额
    """
    default_keys = ['JiShuL', 'JiShuH', 'YangLao', 'YiLiao', 'ShiYe', 'GongShang', 'ShengYu', 'GongJiJin']

    def __init__(self, config_sec):
        self.rates = {}
        try:
            for k in config_sec:
                self.rates[k] = float(config_sec[k])

        except:
            self.__error()

        for key in self.default_keys:
            if key.lower() not in self.rates.keys():
                self.__error()
        try:
            self.JiShuL = self.rates.pop('jishul')
            self.JiShuH = self.rates.pop('jishuh')
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
        # self.is_read_fin = Value('i', 0)
        # self.is_cal_fin = Value('i', 0)
        # self.read_fin_lock = Lock()
        # self.cal_fin_lock = Lock()

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

    def read_data(self, is_error, err_lock, user_q):
        # print('read:{}'.format(os.getpid()))
        try:
            with open(self.data_file) as f:
                for l in f:
                    if is_error.value == 1:
                        return
                    line = l.split(',')
                    # with err_lock:
                    user_q.put([int(line[0]), int(line[1])])
            # with self.read_fin_lock:
            #     self.is_read_fin.value = 1
            # print('read completed')
            user_q.put(['READ', 'FIN'])

        except:
            with err_lock:
                is_error.value = 1
            return

    def cal_data(self, is_error, err_lock, user_q, out_q):
        # print('cal:{} online'.format(os.getpid()))
        try:
            while 1:
                # with err_lock:
                if is_error.value == 1:
                    return

                if not user_q.empty():
                    user_num, user_salary = user_q.get()
                    # print('cal:{} got {} {} '.format(os.getpid(), user_num, user_salary))
                    if user_num == 'READ' and user_salary == 'FIN':
                        user_q.put(['READ', 'FIN'])
                        # print('cal:{} quit'.format(os.getpid()))
                        break
                    else:
                        user_insure = self.config.cal_insure_amount(user_salary)
                        user_income_tax = self.cal_income_tax(user_salary)
                        user_actual_income = user_salary - user_insure - user_income_tax
                        output_list = [user_num, user_salary, user_insure, user_income_tax, user_actual_income]

                        out_q.put(output_list)
                        # print('cal:{} put {}'.format(os.getpid(), output_list))

            # with self.cal_fin_lock:
            #     self.is_cal_fin.value += 1
            out_q.put(['CAL', 'FIN'])
        except:
            with err_lock:
                is_error.value = 1
            return

    def write_data(self, is_error, err_lock, out_q, cal_procs):
        # print('write:{}'.format(os.getpid()))
        try:
            f = open(self.dump_file, 'w')
            fin_flags_recv = 0
            while 1:
                # with err_lock:
                if is_error.value == 1:
                    f.close()
                    return

                if not out_q.empty():
                    output_data = out_q.get()
                    # print('write:{} got {}'.format(os.getpid(), output_data))
                    if output_data[0] == 'CAL' and output_data[1] == 'FIN':
                        fin_flags_recv += 1
                        if fin_flags_recv >= cal_procs:
                            f.close()
                            return
                    else:
                        user_info = '{0},{1},{2},{3},{4},{5}\n'.format(str(output_data[0]),
                                                                       str(output_data[1]),
                                                                       format(output_data[2], ".2f"),
                                                                       format(output_data[3], ".2f"),
                                                                       format(output_data[4], ".2f"),
                                                                       datetime.strftime(datetime.now(),
                                                                                         '%Y-%m-%d %H:%M:%S'))
                        f.write(user_info)
        except:
            # print('write error')
            f.close()
            with err_lock:
                is_error.value = 1
            return


def main(argv):
    if len(argv) < 7:
        p_error()
    else:
        # ./calculator.py -c /home/shiyanlou/test.cfg -d /home/shiyanlou/user.csv -o /tmp/gongzi.csv
        try:
            opts, args = getopt.getopt(argv[1:], 'C:c:d:o:', [])
        except getopt.GetoptError as e:
            p_error()

        cfg_file = None
        cfg_city = 'DEFAULT'
        user_file = None
        output_file = None

        for o, v in opts:
            if o == '-c':
                cfg_file = v
            elif o == '-C':
                cfg_city = v
            elif o == '-d':
                user_file = v
            elif o == '-o':
                output_file = v
        # print(cfg_file, user_file, output_file)
        # print(cfg_city)

        if cfg_file is None or user_file is None or output_file is None:
            p_error()
        con_parser = configparser.ConfigParser()
        try:
            con_parser.read(cfg_file)
        except:
            p_error()

        conf = Config(con_parser[cfg_city.upper()])
        users = UserData(conf, user_file, output_file)

        # Multiprocessing
        # 错误flag，置位后所有进程停止工作，退出程序
        is_error = Value('i', 0)

        # 从用户信息中读取，即将计算个税的队列
        user_q = Queue(maxsize=500)

        # 即将写入到文件的队列
        out_q = Queue(maxsize=500)

        # Lock
        err_lock = Lock()

        cal_procs = 3

        p_read = Process(target=users.read_data, args=(is_error, err_lock, user_q,))
        p_cals = [Process(target=users.cal_data, args=(is_error, err_lock, user_q, out_q,)) for x in range(cal_procs)]
        p_write = Process(target=users.write_data, args=(is_error, err_lock, out_q, cal_procs, ))

        time_start = datetime.now()
        p_read.start()
        for p in p_cals:
            p.start()
        p_write.start()

        p_read.join()
        for p in p_cals:
            p.join()
        time_stop = datetime.now()
        # print('elapsed time: {:2f} seconds'.format((time_stop - time_start).total_seconds()))
        p_write.join()

        if is_error.value == 1:
            p_error()


def p_error():
    print('Parameter Error')
    exit(1)


if __name__ == '__main__':
    main(sys.argv)
    exit(0)
