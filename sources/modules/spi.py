#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: spi
# Created on: 2022/11/22

from ch347api import CH347HIDDev
from ch347api.spi import VENDOR_ID, PRODUCT_ID
import struct
import numpy as np
import time
from i2cylib.utils.bytes import random_keygen


def __test_unit_generate_frame(num):
    header = [0x5a, 0xa5]
    payload = np.random.randint(0, 255, 3 * 4 * num, dtype=np.int32)
    tail = [0xe8, 0x8e]
    return bytes(header + payload.tolist() + tail)


def __decode_frame(data, num_data_per_frame=100, algorithm_num=0):
    header = data[:2]
    tail = data[-2:]
    if header != b"\x5a\xa5" or tail != b"\xe8\x8e":
        return False, None

    if algorithm_num == 0:  # use numpy
        res = np.frombuffer(data, offset=2, count=3 * num_data_per_frame, dtype=np.int32)
        res = res.reshape((num_data_per_frame, 3))

    elif algorithm_num == 1:  # use struct
        res = []
        for i in range(num_data_per_frame):
            res.append(struct.unpack("iii", data[2 + (i * 4 * 3):2 + ((i + 1) * 4 * 3)]))

    else:
        res = []

    return res


class FPGA_SPI(CH347HIDDev):

    def __init__(self, test=False):
        """
        initialize SPI communication interface with topology: FPGA --(SPI)-- CH347 --(USB)-- HostMachine. The default
        clock speed is 60MHz
        """
        super().__init__(VENDOR_ID, PRODUCT_ID, 1)
        if not test:
            self.init_SPI(0, mode=1)
            self.set_CS1()


if __name__ == '__main__':
    test_data_per_frame = 1000

    test_data = __test_unit_generate_frame(test_data_per_frame)
    t0 = time.time()
    test_decoded = __decode_frame(test_data, num_data_per_frame=test_data_per_frame, algorithm_num=0)
    ts = time.time() - t0
    print("algor 0 time spent: {:.4f} ms".format(ts * 1000))
    print("decoded: ")
    for i in range(3):
        print("  ", test_decoded[i])

    t0 = time.time()
    test_decoded = __decode_frame(test_data, num_data_per_frame=test_data_per_frame, algorithm_num=1)
    ts = time.time() - t0
    print("algor 1 time spent: {:.4f} ms".format(ts * 1000))
    print("decoded: ")
    for i in range(3):
        print("  ", test_decoded[i])
