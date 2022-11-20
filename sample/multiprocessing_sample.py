#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: multiprocessing_sample
# Created on: 2022/10/3

from multiprocessing import Process, Value, Array


class test:

    def __init__(self):
        self.num = Value('d', 0.0)
        self.arr = Array('i', range(10))
        self.p = Process(target=self.f)

    def start(self):

        self.p.start()

    def join(self):
        if self.p.is_alive():
            self.p.join()

    def print(self):
        print(self.num.value)
        print(self.arr[:])

    def f(self):
        self.num.value = 3.1415927
        for i in range(len(self.arr)):
            self.arr[i] = -self.arr[i]


if __name__ == '__main__':

    t = test()
    t.start()
    t.join()
    t.print()
