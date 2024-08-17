#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: uart
# Created on: 2022/12/14

import threading
import time
import serial

GPS_DEVICE = "/dev/ttyACM0"
GPS_BR = 9600

DEBUG = False

class Degree:

    def __init__(self, degree, minute):
        self.degree: float = degree
        self.minute: float = minute

    def as_degree(self):
        return self.degree + self.minute / 60

    def as_minute(self):
        return self.degree * 60 + self.minute


class GPS:

    def __init__(self, device, baud_rate=9600, timeout=0.1, timezone_offset=8):
        try:
            self.__clt = serial.Serial(device, baud_rate, timeout=timeout)
        except Exception as err:
            if DEBUG:
                print("failed to open device, but debug mode is on, proceeding without actual GPS device")
            else:
                raise err

        self.debug = DEBUG

        self.__threads = []
        self.__live = False
        self.timezone_offset = timezone_offset

        self.utc_ts: float = 0.0  # timestamp
        self.loc_status: bool = False
        self.latitude: Degree = Degree(0, 0)
        self.longitude: Degree = Degree(0, 0)
        self.north_hemisphere: bool = True
        self.east_longitude: bool = True
        self.ground_speed: float = 0.0
        self.ground_direction: float = 0.0

        self.file_io = None
        self.filename = None

        self.flag_gps_dump = False

    def start(self):

        # create thread
        if not self.debug:
            self.__threads.append(threading.Thread(target=self._receiver))
            self.__live = True
        else:
            self.loc_status = True

        # run threads
        [ele.start() for ele in self.__threads]

    def set_gps_file(self, filename):
        self.filename = filename
        self.file_io = open(filename, "wb")
        self.file_io.close()

    def enable_gps_dump(self, enabled=True):
        self.flag_gps_dump = enabled

    def read_raw(self, timeout=None):
        if timeout is not None:
            self.__clt.timeout = timeout
        return self.__clt.readline().decode()

    def get_realtime(self) -> time.struct_time:
        ret = self.utc_ts + self.timezone_offset * 3600
        return time.localtime(ret)

    def manually_update(self, timeout=2) -> bool:
        if self.debug:
            return True
        else:
            raw = self.read_raw(timeout)

            # print("GPS DEBUG:", raw)

        if len(raw) < 6:
            return False
        else:
            try:
                if self.filename is not None and self.flag_gps_dump:
                    self.file_io = open(self.filename, "a")
                    self.file_io.write(raw)
                    self.file_io.close()

                raw = raw.split(",")
                if raw[0] != "$GNRMC":
                    return False

                if raw[1] and raw[9]:
                    self.utc_ts = time.mktime(time.strptime(raw[9] + raw[1], "%d%m%y%H%M%S.00"))

                if raw[2]:
                    self.loc_status = raw[2] == "A"

                if raw[3]:
                    self.latitude.degree = float(raw[3][0:2])
                    self.latitude.minute = float(raw[3][2:])

                if raw[4]:
                    self.north_hemisphere = raw[4] == "N"

                if raw[5]:
                    self.longitude.degree = float(raw[5][0:3])
                    self.longitude.minute = float(raw[5][3:])

                if raw[6]:
                    self.east_longitude = raw[6] == "E"

                if raw[7]:
                    self.ground_speed = float(raw[7]) * 1.85 / 3.6

                if raw[8]:
                    self.ground_direction = float(raw[8])

            except Exception as err:
                print("GPS error:", err)
                return False
        return True

    def _receiver(self):
        while self.__live:
            raw = self.read_raw()
            if DEBUG:
                print("read raw: {}".format(raw))
            if len(raw) < 6:
                continue
            else:
                try:
                    raw = raw.split(",")
                    if raw[0] != "$GNRMC":
                        continue

                    if raw[1] and raw[9]:
                        self.utc_ts = time.mktime(time.strptime(raw[9] + raw[1], "%d%m%y%H%M%S.00"))

                    if raw[2]:
                        self.loc_status = raw[2] == "A"

                    if raw[3]:
                        self.latitude.degree = float(raw[3][0:2])
                        self.latitude.minute = float(raw[3][2:])

                    if raw[4]:
                        self.north_hemisphere = raw[4] == "N"

                    if raw[5]:
                        self.longitude.degree = float(raw[5][0:3])
                        self.longitude.minute = float(raw[5][3:])

                    if raw[6]:
                        self.east_longitude = raw[6] == "E"

                    if raw[7]:
                        self.ground_speed = float(raw[7]) * 1.85 / 3.6

                    if raw[8]:
                        self.ground_direction = float(raw[8])

                except Exception as err:
                    print("GPS error:", err)
                    continue

    def close(self):
        self.__live = False
        [ele.join() for ele in self.__threads]
        self.__threads.clear()
        self.__clt.close()


if __name__ == '__main__':
    import os
    gps_test = GPS(GPS_DEVICE, GPS_BR)
    gps_test.start()
    while True:
        try:
            # print(gps_test.read_raw(), end="")
            lat_sign = "S"
            if gps_test.north_hemisphere:
                lat_sign = "N"
            long_sign = "W"
            if gps_test.east_longitude:
                long_sign = "E"
            print(f"---- GPS status: {gps_test.loc_status} ----\n"
                  f"time now: {time.strftime('%Y-%m-%d %H:%M:%S', gps_test.get_realtime())}\n"
                  f"latitude: {lat_sign} {gps_test.latitude.degree}°{gps_test.latitude.minute}'\n"
                  f"longitude: {long_sign} {gps_test.longitude.degree}°{gps_test.longitude.minute}'\n"
                  f"speed: {gps_test.ground_speed:.2f} m/s\n"
                  f"towards: {gps_test.ground_direction}°")
            if gps_test.loc_status:
                print(gps_test.get_realtime(), time.time())
                rt_sys = time.strftime("%m%d%H%M%y.%S", gps_test.get_realtime())
                os.system(f"sudo date {rt_sys}")
                print(time.time())
            time.sleep(1)
        except KeyboardInterrupt:
            break

    gps_test.close()
