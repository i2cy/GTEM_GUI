#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: spidev
# Created on: 2023/3/18

import spidev
import time
import numpy as np
from queue import Empty
from multiprocessing import Process, Queue, Manager

if __name__ == "__main__":
    from i2c import FPGACtl
else:
    from .i2c import FPGACtl

SPI_DEV = (1, 0)
MAX_FREQ = 48_000_000
BITS_PER_WORD = 8
SPI_MODE = 0b00

DATA_BATCH = 60
DATA_FRAME_SIZE = 3 * 4


class FPGACommunication:

    def __init__(self, to_file_only: bool = False):

        self.to_file_only = to_file_only
        self.mp_status = Manager().dict({"live": True,
                                         "running": False,
                                         "file_lock": True,
                                         "filename": ""})

        self.mp_raw_data_queue = Queue(200_000 // DATA_BATCH)
        self.mp_ch1_data_queue_x20 = Queue(200_000 // DATA_BATCH // 20)
        self.mp_ch2_data_queue_x20 = Queue(200_000 // DATA_BATCH // 20)
        self.mp_ch3_data_queue_x20 = Queue(200_000 // DATA_BATCH // 20)

        self.spi_dev = spidev.SpiDev()
        self.spi_dev.open(*SPI_DEV)
        self.spi_dev.max_speed_hz = MAX_FREQ
        self.spi_dev.mode = SPI_MODE
        self.spi_dev.bits_per_word = BITS_PER_WORD

        self.filename = ""
        self.file_io = None

        self.processes = []

        self.start()

    def set_output_file(self, filename):
        self.mp_status["filename"] = filename

    def proc_spi_receiver(self):
        while self.mp_status["live"]:
            if not self.mp_status["running"]:  # 待机状态
                time.sleep(0.000_001)
                continue
            try:
                data = self.spi_dev.readbytes(DATA_BATCH * DATA_FRAME_SIZE)
            except TimeoutError:
                continue
            self.mp_raw_data_queue.put(data)

    def proc_data_process(self):
        ch1_batch = []
        ch2_batch = []
        ch3_batch = []
        cnt = 0

        file_closed = True
        file_io = None

        while self.mp_status["live"]:
            if not self.mp_status["running"]:  # 待机状态
                if not file_closed:
                    file_io.close()
                    file_closed = True
                    self.mp_status["file_lock"] = False
                time.sleep(0.000_001)
                continue

            if file_closed:
                file_io = open(self.mp_status["filename"], "wb")
                file_closed = False
                self.mp_status["file_lock"] = True

            try:
                frame = self.mp_raw_data_queue.get()
            except Empty:
                continue

            byte_array = bytes(frame)

            file_io.write(bytes(frame))  # write to file in sub process

            dt = np.dtype(np.int32)
            dt.newbyteorder(">")

            frame = np.frombuffer(byte_array, dtype=dt)

            if not self.to_file_only:
                if cnt < 20:
                    ch1_batch.extend(frame[0::3].tolist())
                    ch2_batch.extend(frame[1::3].tolist())
                    ch3_batch.extend(frame[2::3].tolist())
                    cnt += 1
                else:
                    self.mp_ch1_data_queue_x20.put(ch1_batch)
                    self.mp_ch2_data_queue_x20.put(ch2_batch)
                    self.mp_ch3_data_queue_x20.put(ch3_batch)
                    ch1_batch.clear()
                    ch2_batch.clear()
                    ch3_batch.clear()

                ch1_batch.extend(frame[0::3])
                ch2_batch.extend(frame[1::3])
                ch3_batch.extend(frame[2::3])

                cnt = 0

    def start(self):
        self.mp_status["live"] = True  # start signal

        self.processes.append(Process(target=self.proc_spi_receiver))
        self.processes.append(Process(target=self.proc_data_process))

        [ele.start() for ele in self.processes]

    def stop(self):
        self.close()
        self.mp_status["live"] = False  # stop signal
        [ele.join() for ele in self.processes]

    def open(self):
        self.mp_status["running"] = True

    def close(self):
        self.mp_status["running"] = False
        while self.mp_status["file_lock"]:
            time.sleep(0.001)


def fpga_demo():
    test_file = "test.bin"

    ctl = FPGACtl("/dev/i2c-2")
    com = FPGACommunication(to_file_only=True)
    com.set_output_file(test_file)
    ctl.enable_channels(True, True, True)
    ctl.set_sample_rate_level(0x0d)
    ctl.set_amp_rate_of_channels(0x0f, 0x0f, 0x0f)
    print("starting communication receiver")
    com.open()
    time.sleep(1)
    print("starting FPGA transmission")
    ctl.start_FPGA()
    time.sleep(1)
    print("finishing test")
    com.close()
    com.stop()
    ctl.stop_FPGA()

    with open(test_file, "rb") as f:
        data = f.read()
        print("received data length: {}".format(len(data)))
        print("total frames: {}".format(len(data) / DATA_FRAME_SIZE))
        dt = np.dtype(np.int32)
        dt.newbyteorder(">")
        first4 = np.frombuffer(data[0:4 * DATA_FRAME_SIZE], dtype=dt)
        print("first 4 data of ch1: \n{}\n{}\n".format(first4[0::3], [hex(ele)[2:].upper() for ele in first4[0::3]]))
        print("first 4 data of ch2: \n{}\n{}\n".format(first4[1::3], [hex(ele)[2:].upper() for ele in first4[1::3]]))
        print("first 4 data of ch3: \n{}\n{}\n".format(first4[2::3], [hex(ele)[2:].upper() for ele in first4[2::3]]))
        f.close()


def spi_demo():
    master = False
    print("starting SPI Universal Receiver at {} bytes per frame".format(DATA_FRAME_SIZE * DATA_BATCH))

    if master:
        spi = spidev.SpiDev()
        spi.open(1, 0)
        spi.max_speed_hz = 10_000_000
        spi.mode = 0b00
        spi.bits_per_word = 8
        spi.cshigh = False
        spi.no_cs = False
        for i in range(1):
            spi.writebytes(1 * b'\x00\x01\x02\x03\x04\x05\x06\x07')
            print("received: ", spi.readbytes(128))

    else:
        spi = spidev.SpiDev()
        spi.open(1, 0)
        spi.max_speed_hz = 48_000_000
        spi.mode = 0b00
        spi.bits_per_word = 8
        while True:
            try:
                print("received: ", [hex(ele) for ele in spi.readbytes(DATA_FRAME_SIZE * DATA_BATCH)])
            except TimeoutError as err:
                continue


if __name__ == '__main__':
    import os

    os.system("sudo chown -Rh pi /dev")

    fpga_demo()

    spi_demo()
