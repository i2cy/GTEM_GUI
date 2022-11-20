#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: gtem
# Created on: 2022/9/15


import numpy as np
import os
import matplotlib.pyplot as plt


class Gtem24:

    def __init__(self, sample_rate=25000, emit_freq=25, gain=0.25,
                 peak_point=127, data=None):
        self.sample_rate = sample_rate
        self.emit_freq = emit_freq
        self.gain = gain

        self.peak_point = peak_point

        self.__k_T = self.sample_rate / self.emit_freq
        self.__k_half_of_T = self.__k_T // 2
        self.__k_pulse_length = int(self.__k_T / 4 * 0.9)

        self.__data = data

    def updateData(self, data: np.ndarray):
        self.__data = data

    def gateTraceSecFieldExtract(self, t_len, filter_level=1):
        peak_point = self.peak_point
        add_time = self.emit_freq * t_len
        data_raw = self.__data.copy()

        data_ban = np.zeros((add_time, self.__k_pulse_length))

        if filter_level == 1:
            for k in range(add_time):
                for x in range(self.__k_pulse_length):
                    if data_raw[peak_point] > 0:
                        if data_raw[x + peak_point] > data_raw[x + peak_point - 1]:
                            deri = data_raw[x + peak_point] - data_raw[x + peak_point - 1]
                            data_raw[x + peak_point] -= deri / 2
                            data_raw[x + peak_point - 1] += deri / 2
                    else:
                        if data_raw[x + peak_point] < data_raw[x + peak_point - 1]:
                            deri = data_raw[x + peak_point - 1] - data_raw[x + peak_point]
                            data_raw[x + peak_point] += deri / 2
                            data_raw[x + peak_point - 1] -= deri / 2

                peak_point += int(self.__k_T)

        peak_point = self.peak_point
        flag = False
        if data_raw[peak_point] > 0:
            flag = True

        for k in range(add_time):
            for x in range(self.__k_pulse_length):
                if flag:
                    data_ban[k][x] = (data_raw[x + peak_point - 1] -
                                      data_raw[int(x + peak_point - 1 + self.__k_half_of_T)]) / 2
                else:
                    data_ban[k][x] = (-data_raw[x + peak_point - 1] +
                                      data_raw[int(x + peak_point - 1 + self.__k_half_of_T)]) / 2
            peak_point += int(self.__k_T)

        sin_noise_sum = np.sum(data_ban, 0) / add_time
        x = np.linspace(1, self.__k_pulse_length, len(sin_noise_sum))
        x = x / (self.sample_rate / 1000)
        # print(sin_noise_sum)

        return x, sin_noise_sum


class Gtem24File(object):

    def __init__(self, filename: str, sample_rate=25000,
                 emit_freq=25, peak_point=127, gain=0.25):
        self.filename = filename
        self.sample_rate = sample_rate
        self.emit_freq = emit_freq
        self.peak_point = peak_point
        self.gain = gain

        self.reserved = b"\x00"

        self.__k_alpha = self.sample_rate / self.emit_freq
        self.__k_beta = int(self.__k_alpha / 2)
        self.__k_pulse_length = int(self.__k_alpha / 4 * 0.9)

        self.__data = None

        t = []

        if os.path.exists(filename) and os.path.isfile(filename):
            with open(self.filename, "rb") as f_raw:
                while True:
                    data = int().from_bytes(f_raw.read(3), "little", signed=True)
                    if not data:
                        break
                    f_raw.read(1)
                    # p = int().from_bytes(f_raw.read(1), "little", signed=False)
                    data = (data / 8388607) * 4096000 / self.gain
                    t.append(data)
            self.__data = np.array(t, dtype=np.float32)

    def __getitem__(self, item):
        return self.__data[item]

    def __iter__(self):
        return self.__data

    def __len__(self):
        return len(self.__data)

    def setData(self, data: np.ndarray):
        self.__data = data

    def addData(self, data, proc=True):
        # if proc:
        #     self.append((data / 8388607) * 4096000 / self.gain)
        # else:
        #     self.append(data)
        pass

    def updateReserve(self, val: bytes):
        assert len(val) == 1
        self.reserved = val

    def updateData(self, data, proc=True):
        # self.pop(0)
        # if proc:
        #     self.append((data / 8388607) * 4096000 / self.gain)
        # else:
        #     self.append(data)
        pass

    def asNumpy(self):
        return self.__data

    def saveToFile(self, filename=None):
        if filename is None:
            filename = self.filename
        ret = 0
        with open(filename, "wb") as f_raw:
            for i, data in enumerate(self):
                data = data * self.gain / 4096 * 8388.607
                data = round(data)
                ret += f_raw.write(int(data).to_bytes(3, "little", signed=True))
                ret += f_raw.write(self.reserved)
            f_raw.close()
        return ret

    def gateTraceSecFieldExtract(self, t_len, filter_level=1):
        peak_point = self.peak_point
        add_time = self.emit_freq * t_len
        data_raw = self.asNumpy().copy()

        data_ban = np.zeros((add_time, self.__k_pulse_length))

        if filter_level == 1:
            for k in range(add_time):
                for x in range(self.__k_pulse_length):
                    if data_raw[peak_point] > 0:
                        if data_raw[x + peak_point] > data_raw[x + peak_point - 1]:
                            deri = data_raw[x + peak_point] - data_raw[x + peak_point - 1]
                            data_raw[x + peak_point] -= deri / 2
                            data_raw[x + peak_point - 1] += deri / 2
                    else:
                        if data_raw[x + peak_point] < data_raw[x + peak_point - 1]:
                            deri = data_raw[x + peak_point - 1] - data_raw[x + peak_point]
                            data_raw[x + peak_point] += deri / 2
                            data_raw[x + peak_point - 1] -= deri / 2

                peak_point += int(self.__k_alpha)

        peak_point = self.peak_point
        flag = False
        if data_raw[peak_point] > 0:
            flag = True

        for k in range(add_time):
            for x in range(self.__k_pulse_length):
                if flag:
                    data_ban[k][x] = (data_raw[x + peak_point - 1] -
                                      data_raw[int(x + peak_point - 1 + self.__k_beta)]) / 2
                else:
                    data_ban[k][x] = (-data_raw[x + peak_point - 1] +
                                      data_raw[int(x + peak_point - 1 + self.__k_beta)]) / 2
            peak_point += int(self.__k_alpha)

        sin_noise_sum = np.sum(data_ban, 0) / add_time
        x = np.linspace(1, self.__k_pulse_length, len(sin_noise_sum))
        x = x / (self.sample_rate / 1000)
        # print(sin_noise_sum)

        return x, sin_noise_sum

    def drawSecFieldPlot(self, t_len, filter_level=1):
        sig_sum, data = self.gateTraceSecFieldExtract(t_len, filter_level)
        x = np.linspace(1, self.__k_pulse_length, len(sig_sum))
        plt.loglog(x / (self.sample_rate / 1000), sig_sum)
        plt.grid(axis="both")
        plt.show()


if __name__ == '__main__':
    f = Gtem24File("../../sample/GTEM_tests/dataTEM1/220102_100601.bin")
    f.drawSecFieldPlot(60)
