#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: multiprocessing_with_numpy
# Created on: 2022/10/3

import ctypes
import time
import multiprocessing
import numpy as np

NUM_PROCESS = multiprocessing.cpu_count()

size = 1000000


def worker(index):
    main_nparray = np.frombuffer(shared_array_base[index], dtype=ctypes.c_double)
    for i in range(10000):
        main_nparray[:] = index + i
    return index


if __name__ == "__main__":
    shared_array_base = []
    for _ in range(NUM_PROCESS):
        shared_array_base.append(multiprocessing.Array("d", size, lock=False))

    pool = multiprocessing.Pool(processes=NUM_PROCESS)

    a = time.time()
    result = pool.map(worker, range(NUM_PROCESS))
    b = time.time()
    print(b-a)
    #print(result)


    for i in range(NUM_PROCESS):
        main_nparray = np.frombuffer(shared_array_base[i], dtype=ctypes.c_double)
        print(main_nparray)
        print(type(main_nparray))
        print(main_nparray.shape)

    # 73.216189146
    # 73.2605750561
    # 73.3307318687
    # 73.4090409279
    # 73.4219110012