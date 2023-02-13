#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: uart
# Created on: 2022/12/14

import serial

GPS_DEVICE = "/dev/ttyACM0"
GPS_BR = 9600


class GPS:

    def __init__(self, device, baud_rate=9600):
        self.__clt = serial.Serial(device, baud_rate)

    def read_raw(self):
        return self.__clt.readline().decode()


    def _receiver(self):
        pass

    def close(self):
        self.__clt.close()


if __name__ == '__main__':
    gps_test = GPS(GPS_DEVICE, GPS_BR)
    while True:
        try:
            print(gps_test.read_raw(), end="")
        except KeyboardInterrupt:
            break

    gps_test.close()
