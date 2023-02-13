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

    def __thread_receiver(self):
        pass


if __name__ == '__main__':
    import random
    from hashlib import sha256

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


    def generate_random_data(length=50):
        res = []
        for i in range(length):
            res.append(int(random.random() * 255))
        return bytes(res)


    test_dev = CH347HIDDev(VENDOR_ID, PRODUCT_ID, 1)
    print("Manufacturer: %s" % test_dev.get_manufacturer_string())
    print("Product: %s" % test_dev.get_product_string())
    print("Serial No: %s" % test_dev.get_serial_number_string())
    test_dev.init_SPI(1, mode=1)
    test_dev.set_CS1()
    test_data_frame_length = 8192

    data = generate_random_data(test_data_frame_length)

    # while True:
    #     print(bytes(test_dev.spi_read(16)).hex())

    feed = test_dev.spi_read_write(data)
    print("R/W loop accusation test result: {}".format(bytes(feed) == data))
    t0 = time.time()
    for ele in range(200000 // (test_data_frame_length // 4)):
        test_dev.set_CS1(True)
        feed = test_dev.spi_read_write(data)
        test_dev.set_CS1(False)
    print("1 sec of gtem data trans time spent {:.2f} ms".format((time.time() - t0) * 1000))

    test_read_length = 4 * 3 * 200000

    print("reading {} bytes of data from device".format(test_read_length))
    t0 = time.time()
    test_dev.set_CS1(True)
    test_dev.spi_read(test_read_length)
    test_dev.set_CS1(False)
    print("data length: {}, time spent {:.2f} ms".format(len(feed), (time.time() - t0) * 1000))

    print("testing 512MB of data (8K per frame) trans accusation")
    data = generate_random_data(test_data_frame_length)
    for i in range(65536):
        t0 = time.time()
        test_dev.set_CS1(True)
        test_dev.spi_read_write(data)
        test_dev.set_CS1(False)
        # delay = 0.0004*8 - time.time() + t0
        # if delay > 0:
        #     time.sleep(delay)
        # else:
        #     print("too fast, timeout: {}us".format(int(delay * 1000000)))
        print("time: {}us".format(int((time.time() - t0) * 1000000)))

    test_dev.close()
