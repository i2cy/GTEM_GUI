#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: data
# Created on: 2022/9/11

import time
import numpy as np
from multiprocessing import Array, Process, Queue, Value
import ctypes


class PlotBuf:

    def __init__(self, buf_length=25000 * 5, sample_rate=25000, freq=25):
        self.__data = DataBuf(buf_length)
        self.__time = TimeBuf(buf_length, sample_rate)
        self.__last_fetch_ts = time.time()
        self.__ds_cnt = -1
        self.__freq = freq

    def __next__(self):
        if self.__index_out > self.buf_length:
            raise StopIteration
        ret = self[self.__index_out]
        self.__index_out += 1
        return ret

    def __iter__(self):
        self.__index_out = 0

        return self

    def __getitem__(self, item):
        return [self.__time[item], self.__data[item]]

    def reset(self, buf_length=None, sample_rate=None, down_sampling=None, freq=None):
        if down_sampling is not None:
            self.down_sampling = down_sampling
        if freq is not None:
            self.__freq = freq
        self.__ds_cnt = -1
        self.__last_fetch_ts = time.time()
        self.__data.reset(buf_length)
        self.__time.reset(buf_length, sample_rate)

    def updateOne(self, data, timestamp=None):
        self.__data.updateOne(data)
        self.__time.updateOne(timestamp)

    def getBuf(self, latest=25000):
        dt = int((time.time() - self.__last_fetch_ts) * self.__freq) / self.__freq
        self.__last_fetch_ts = time.time()
        return dt, (self.__time.asNumpy(latest),
                    self.__data.asNumpy(latest))


class TimeBuf(object):

    def __init__(self, buf_length=2000, sample_rate=200):

        self.buf_length = buf_length
        self.sample_rate = sample_rate

        t0 = buf_length / sample_rate

        self.__data = np.linspace(-t0, 0, self.buf_length, dtype=np.float32)
        self.__index_in = 0
        self.__index_out = 0
        self.t0 = time.time()

    def __len__(self):
        return len(self.__data)

    def __getitem__(self, item):
        if isinstance(item, int):
            index = self.__index_in + item
            if index >= self.buf_length:
                index -= self.buf_length
            return self.__data[index]
        elif isinstance(item, slice):
            return self.asNumpy()[item]

    def __next__(self):
        if self.__index_out > self.buf_length:
            raise StopIteration
        ret = self[self.__index_out]
        self.__index_out += 1
        return ret

    def __iter__(self):
        self.__index_out = 0

        return self

    def asNumpy(self, latest=25000):
        if self.__index_in > latest:
            return self.__data[self.__index_in - latest:self.__index_in]
        else:
            return np.concatenate((self.__data[self.buf_length + self.__index_in - latest:],
                                   self.__data[:self.__index_in]))

    def reset(self, buf_length=None, sample_rate=None):
        self.__index_in = 0
        if not buf_length is None:
            self.buf_length = buf_length
        if not sample_rate is None:
            self.sample_rate = sample_rate

        t0 = buf_length / sample_rate

        self.__data = np.linspace(-t0, 0, self.buf_length, dtype=np.float64)
        self.__index_in = 0
        self.t0 = time.time()

    def setT0(self, t0):
        self.t0 = t0

    def updateOne(self, timestamp=None):
        if timestamp is None:
            timestamp = time.time() - self.t0
        self.__data[self.__index_in] = timestamp
        self.__index_in += 1
        if self.__index_in >= self.buf_length:
            self.__index_in = 0


class DataBuf(object):

    def __init__(self, buf_length=2000):
        self.buf_length = buf_length
        self.__data = np.zeros(self.buf_length, dtype=np.float32)
        self.__filtered_data = np.zeros(self.buf_length, dtype=np.float32)
        # self.__data = Array("f", self.buf_length)
        # self.__filtered_data = Array("f", self.buf_length)
        # self.__pipe_queue = Queue(8192)
        # self.__control = Value(ctypes.c_bool, True)

        # self.__index_in = Value("d", 0)
        self.__index_in = 0
        self.__index_out = 0

        # self.__p = Process(target=self.multiCoreProc)
        # self.__p.start()

    def __len__(self):
        return len(self.__data)

    def __getitem__(self, item):
        if isinstance(item, int):
            index = self.__index_in + item
            if index >= self.buf_length:
                index -= self.buf_length
            return self.__data[index]
        elif isinstance(item, slice):
            return self.asNumpy()[item]

    def __next__(self):
        if self.__index_out > self.buf_length:
            raise StopIteration
        ret = self[self.__index_out]
        self.__index_out += 1
        return ret

    def __iter__(self):
        self.__index_out = 0

        return self

    def getFiltered(self):
        return self.__filtered_data

    def asNumpy(self, latest=25000):
        dat = np.frombuffer(self.__data, dtype=np.float32)
        if self.__index_in > latest:
            return dat[self.__index_in - latest:self.__index_in]
        else:
            return np.concatenate((dat[self.buf_length + self.__index_in - latest:],
                                   dat[:self.__index_in]))

    # def kill(self):
    #     if self.__p.is_alive():
    #         self.__control.value = False
    #         self.__pipe_queue.put(0.0)
    #         self.__p.join()

    def reset(self, buf_length=None):
        # if self.__p.is_alive():
        #     self.__control.value = False
        #     self.__pipe_queue.put(0.0)
        #     self.__p.join()
        #
        # while not self.__pipe_queue.empty():
        #     try:
        #         self.__pipe_queue.get_nowait()
        #     except Exception:
        #         continue
        #
        # if buf_length == self.buf_length:
        #     for i in range(self.buf_length):
        #         self.__data[i] = 0.0
        #         self.__filtered_data[i] = 0.0
        # else:
        #     self.buf_length = buf_length
        #     self.__data = Array("f", self.buf_length)
        #     self.__filtered_data = Array("f", self.buf_length)
        #
        # self.__control.value = True
        #
        # self.__index_in.value = 0
        if buf_length is not None:
            self.buf_length = buf_length

        self.__data = np.zeros(self.buf_length, dtype=np.float32)
        self.__filtered_data = np.zeros(self.buf_length, dtype=np.float32)

        self.__index_in = 0
        self.__index_out = 0

        # self.__p = Process(target=self.multiCoreProc)

    def updateOne(self, data):
        # self.__pipe_queue.put(data)
        self.__data[self.__index_in] = data
        self.__index_in += 1
        if self.__index_in >= self.buf_length:
            self.__index_in = 0


