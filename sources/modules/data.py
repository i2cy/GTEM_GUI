#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: data
# Created on: 2022/9/11

import time
import numpy as np
from multiprocessing import Array, Process, Queue, Value, Pool
import ctypes
from i2cylib.utils.logger import Logger


class PlotBuf:

    def __init__(self, buf_length=25000 * 50, sample_rate=25000, freq=25, logger: Logger = None):
        if logger is None:
            # create new logger if not set
            logger = Logger()
        self.__logger = logger

        self.__data = DataBuf(buf_length, self.__logger)
        self.__time = TimeBuf(buf_length, sample_rate, self.__logger)
        self.__last_fetch_ts = time.time()
        self.__ds_cnt = -1
        self.__freq = freq
        self.__sample_rate = sample_rate
        self.__time_offset = time.time()



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
        self.__time_offset = time.time()
        self.__sample_rate = sample_rate

    def updateOne(self, data, timestamp=None):
        self.__data.updateOne(data)
        self.__time.updateOne(timestamp)

    def updateBatch(self, data, x):
        self.__data.updateBatch(data)
        self.__time.updateBatch(x)

    def getBuf(self, latest=25000):
        self.__last_fetch_ts = time.time()
        time_scale = latest / self.__sample_rate
        start_ts = self.__last_fetch_ts + self.__time_offset
        end_ts = start_ts + time_scale

        if start_ts < self.__time[0]:
            self.__time_offset = self.__time[0] - self.__last_fetch_ts

        elif end_ts > self.__time[-1] and self.__time[-1] > 0:
            self.__time_offset = self.__time[-1] - time_scale - self.__last_fetch_ts

        start_index = int(
            (self.__last_fetch_ts + self.__time_offset - self.__time[0]) * self.__sample_rate
        )

        # print("t_min:", self.__time[0], "t_max:", self.__time[-1])
        # print("start:", start_index, "end:", start_index + latest)

        x = self.__time.asNumpy(start_index, start_index + latest)
        y = self.__data.asNumpy(start_index, start_index + latest)

        return x, y


class TimeBuf(object):

    def __init__(self, buf_length=200000 * 10, sample_rate=200, logger: Logger = None):

        if logger is None:
            # create new logger if not set
            logger = Logger()
        self.__logger = logger

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

    def asNumpy(self, start_index=0, end_index=0):
        actual_start = self.__index_in + start_index
        if actual_start >= self.buf_length:
            actual_start -= self.buf_length
        actual_end = self.__index_in + end_index
        if actual_end > self.buf_length:
            actual_end -= self.buf_length - 1

        if actual_start >= actual_end:
            return np.concatenate((self.__data[actual_start:],
                                   self.__data[:actual_end])).copy()
        else:
            return self.__data[actual_start:actual_end].copy()

    def reset(self, buf_length=None, sample_rate=None):
        self.__index_in = 0
        if not buf_length is None:
            self.buf_length = buf_length
        if not sample_rate is None:
            self.sample_rate = sample_rate

        t0 = buf_length / sample_rate

        self.__data = np.zeros(self.buf_length, dtype=np.float32)
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

    def updateBatch(self, timestamp):
        batch_length = len(timestamp)
        left = self.buf_length - self.__index_in
        if batch_length <= left:
            self.__data[self.__index_in:self.__index_in + batch_length] = timestamp
            self.__index_in += batch_length
        else:
            self.__data[self.__index_in:] = timestamp[:left]
            self.__index_in = batch_length - left
            try:
                self.__data[:self.__index_in] = timestamp[left:]
            except Exception as err:
                self.__logger.ERROR(
                    f"[timestamp buffer] time err: index_in: {self.__index_in}, total_data: {batch_length},"
                    f" data_left: {len(timestamp[left:])}, msg: {err}")


class DataBuf(object):

    def __init__(self, buf_length=200000 * 10, logger: Logger = None):

        if logger is None:
            # create new logger if not set
            logger = Logger()
        self.__logger = logger

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

    def asNumpy(self, start_index=0, end_index=0):
        actual_start = self.__index_in + start_index
        if actual_start >= self.buf_length:
            actual_start -= self.buf_length
        actual_end = self.__index_in + end_index
        if actual_end > self.buf_length:
            actual_end -= self.buf_length - 1
        if actual_start >= actual_end:
            return np.concatenate((self.__data[actual_start:],
                                   self.__data[:actual_end])).copy()
        else:
            return self.__data[actual_start:actual_end].copy()

    def reset(self, buf_length=None):
        if buf_length is not None:
            self.buf_length = buf_length

        self.__data = np.zeros(self.buf_length, dtype=np.float32)
        self.__filtered_data = np.zeros(self.buf_length, dtype=np.float32)

        self.__index_in = 0
        self.__index_out = 0

    def updateOne(self, data):
        # self.__pipe_queue.put(data)
        self.__data[self.__index_in] = data
        self.__index_in += 1
        if self.__index_in >= self.buf_length:
            self.__index_in = 0

    def updateBatch(self, data):
        batch_length = len(data)
        left = self.buf_length - self.__index_in
        if batch_length <= left:
            self.__data[self.__index_in:self.__index_in + batch_length] = data
            self.__index_in += batch_length
        else:
            self.__data[self.__index_in:] = data[:left]
            self.__index_in = batch_length - left
            try:
                self.__data[:self.__index_in] = data[left:]
            except Exception as err:
                self.__logger.ERROR(
                    f"[data buffer] data err: index_in: {self.__index_in}, total_data: {batch_length}, data_left: {len(data[left:])}, msg: {err}")
