#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: spidev
# Created on: 2023/3/18

import spidev


if __name__ == '__main__':
    import os
    os.system("sudo chown -Rh pi /dev")
    master = False

    if master:
        spi = spidev.SpiDev()
        spi.open(1, 0)
        spi.max_speed_hz = 10_000_000
        spi.mode = 0b00
        spi.bits_per_word = 8
        spi.cshigh = False
        spi.no_cs = False
        for i in range(1):
            spi.writebytes(1*b'\x00\x01\x02\x03\x04\x05\x06\x07')
            print("received: ", spi.readbytes(128))

    else:
        spi = spidev.SpiDev()
        spi.open(1, 0)
        spi.max_speed_hz = 50_000_000
        spi.mode = 0b11
        spi.bits_per_word = 8
        while True:
            try:
                print("received: ", [hex(ele) for ele in spi.readbytes(16)])
            except TimeoutError as err:
                continue
