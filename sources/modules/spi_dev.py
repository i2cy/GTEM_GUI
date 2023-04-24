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

DATA_BATCH = 60 * 3
DATA_FRAME_SIZE = 3 * 4


class FPGACom:

    def __init__(self, to_file_only: bool = False, debug=True):

        self.to_file_only = to_file_only
        self.mp_status = Manager().dict({"live": True,
                                         "running": False,
                                         "file_lock": False,
                                         "filename": "",
                                         "debug": debug,
                                         "swapping_file": False})

        self.mp_raw_data_queue = Queue(200_000_000 // DATA_BATCH)
        self.mp_ch1_data_queue_x4 = Queue(200_000_000 // DATA_BATCH // 4)
        self.mp_ch2_data_queue_x4 = Queue(200_000_000 // DATA_BATCH // 4)
        self.mp_ch3_data_queue_x4 = Queue(200_000_000 // DATA_BATCH // 4)

        self.spi_dev = spidev.SpiDev()
        self.spi_dev.open(*SPI_DEV)
        self.spi_dev.max_speed_hz = MAX_FREQ
        self.spi_dev.mode = SPI_MODE
        self.spi_dev.bits_per_word = BITS_PER_WORD

        self.filename = ""
        self.file_io = None

        self.processes = []

    def set_output_file(self, filename):
        self.mp_status["filename"] = filename
        if self.mp_status["file_lock"]:
            print("swapping file")
            self.mp_status["swapping_file"] = True
            while self.mp_status["swapping_file"]:
                time.sleep(0.001)
            print("swapping file completed")

    def proc_spi_receiver(self):
        if self.mp_status["debug"]:
            print("proc_spi_receiver started")
        while self.mp_status["live"]:
            if not self.mp_status["running"]:  # 待机状态
                time.sleep(0.000_001)
                continue
            try:
                data = self.spi_dev.readbytes(DATA_BATCH * DATA_FRAME_SIZE)
            except TimeoutError:
                continue
            self.mp_raw_data_queue.put(data)
        if self.mp_status["debug"]:
            print("proc_spi_receiver stopped")

    def proc_data_process(self):
        ch1_batch = []
        ch2_batch = []
        ch3_batch = []
        cnt = 0

        file_closed = True
        file_io = None

        if self.mp_status["debug"]:
            print("proc_data_process started")

        t_debug = time.time()

        while self.mp_status["live"]:
            if not self.mp_status["running"]:  # 待机状态
                if not file_closed:
                    file_io.close()
                    file_closed = True
                    self.mp_status["file_lock"] = False
                    print("proc_data_process file closed")
                time.sleep(0.000_001)
                continue

            if file_closed:
                file_io = open(self.mp_status["filename"], "wb")
                file_closed = False
                self.mp_status["file_lock"] = True
                print("proc_data_process file opened")

            try:
                frame = self.mp_raw_data_queue.get(timeout=0.5)
            except Empty:
                continue

            if not len(frame):
                continue

            byte_array = bytes(frame)

            if self.mp_status["swapping_file"]:
                file_io.close()
                file_io = open(self.mp_status["filename"], "wb")
                self.mp_status["swapping_file"] = False

            file_io.write(byte_array)  # write to file in sub process

            dt = np.dtype(np.int32)
            dt.newbyteorder(">")

            frame = np.frombuffer(byte_array, dtype=dt)

            frame = frame & 0x00ffffff

            if not self.to_file_only:
                if cnt < 4:
                    ch1_batch.extend(frame[0::3].tolist())
                    ch2_batch.extend(frame[1::3].tolist())
                    ch3_batch.extend(frame[2::3].tolist())
                    cnt += 1
                else:
                    ch1_batch.extend(frame[0::3].tolist())
                    ch2_batch.extend(frame[1::3].tolist())
                    ch3_batch.extend(frame[2::3].tolist())
                    self.mp_ch1_data_queue_x4.put(ch1_batch)
                    self.mp_ch2_data_queue_x4.put(ch2_batch)
                    self.mp_ch3_data_queue_x4.put(ch3_batch)

                    # print(f"put X4 queue once in {time.time() - t_debug:.2f}s,"
                    #       f"\n   ch1 {len(ch1_batch)} ch2 {len(ch2_batch)} ch3 {len(ch3_batch)}")
                    t_debug = time.time()

                    time.sleep(0.002)

                    ch1_batch.clear()
                    ch2_batch.clear()
                    ch3_batch.clear()
                    cnt = 0

        if self.mp_status["debug"]:
            print("proc_data_process stopped")

    def start(self):
        self.mp_status["live"] = True  # start signal

        self.processes.append(Process(target=self.proc_spi_receiver))
        self.processes.append(Process(target=self.proc_data_process))

        [ele.start() for ele in self.processes]

    def debug(self, value: bool = True):
        self.mp_status["debug"] = value

    def kill(self):
        self.close()
        self.mp_status["live"] = False  # stop signal
        [ele.join() for ele in self.processes]
        self.processes.clear()

    def open(self):
        self.mp_status["running"] = True
        while not self.mp_status["file_lock"]:
            time.sleep(0.001)

    def close(self):
        self.mp_status["running"] = False
        while self.mp_status["file_lock"]:
            time.sleep(0.001)


def fpga_demo():
    test_file = "test.bin"

    test_data_ch1 = b"\xa1\xa5\x5a\xa5"
    test_data_ch2 = b"\xa2\xa5\x5a\xa5"
    test_data_ch3 = b"\xa4\xa5\x5a\xa5"

    # test_data_ch1 = b"\xa1\xa2\xa3\xa4"
    # test_data_ch2 = b"\xa5\xa6\xa7\xa8"
    # test_data_ch3 = b"\xa9\xaa\xab\xac"

    ctl = FPGACtl("/dev/i2c-2")
    com = FPGACom(to_file_only=True)
    com.debug(False)
    com.set_output_file(test_file)
    ctl.enable_channels(True, True, True)

    level2str = ["500", "1k", "2k", "4k", "8k", "10k", "20k", "32k", "40k", "80k", "25k", "50k", "100k", "200k", "400k",
                 "800k"]
    print("starting communication receiver")
    com.start()

    for level in range(4, 13):
        print("testing sample rate level:", level2str[level])
        ctl.set_sample_rate_level(level)
        ctl.set_amp_rate_of_channels('1', '1', '1')
        time.sleep(0.5)
        print(" + starting FPGA transmission for 5 seconds")
        com.open()
        ctl.start_FPGA()
        time.sleep(5)
        print(" - finishing transmission")
        com.close()
        time.sleep(0.5)
        ctl.stop_FPGA()
        print(" + testing data integrity")

        with open(test_file, "rb") as f:
            data = f.read()
            print("    received data length: {}".format(len(data)))
            print("    frames: {}".format(len(data) / DATA_FRAME_SIZE))
            dt = np.dtype(np.int32)
            dt.newbyteorder(">")
            first4 = np.frombuffer(data[0:4 * DATA_FRAME_SIZE], dtype=dt)
            sliced = []
            for index, ele in enumerate(data[::4]):
                sliced.append(data[index * 4: (index + 1) * 4])
            print("    first 4 data of ch1: \n    {}\n    {}".format(first4[0::3],
                                                                     [ele.hex().upper() for ele in
                                                                      sliced[0:4 * 3:3]]))
            print("    first 4 data of ch2: \n    {}\n    {}".format(first4[1::3],
                                                                     [ele.hex().upper() for ele in
                                                                      sliced[1:4 * 3:3]]))
            print("    first 4 data of ch3: \n    {}\n    {}".format(first4[2::3],
                                                                     [ele.hex().upper() for ele in
                                                                      sliced[2:4 * 3:3]]))

            f.close()

        print(" = real sample rate: {:.2f} KS/s".format(len(sliced) / 5000))

        correct_ch1 = sum([ele == test_data_ch1 for ele in sliced[0::3]])
        correct_ch2 = sum([ele == test_data_ch2 for ele in sliced[1::3]])
        correct_ch3 = sum([ele == test_data_ch3 for ele in sliced[2::3]])

        for ele in sliced[0::3]:
            if ele != test_data_ch1:
                print(" = Incorrect data example in CH1: {}".format(ele.hex().upper()))
                break

        print(" = CH1 data integrity: {:.2f}% correct of {} samples in total".format(
            100 * (correct_ch1 / (len(sliced) / 3)),
            len(sliced) / 3))
        print(" = CH2 data integrity: {:.2f}% correct of {} samples in total".format(
            100 * (correct_ch2 / (len(sliced) / 3)),
            len(sliced) / 3))
        print(" = CH3 data integrity: {:.2f}% correct of {} samples in total".format(
            100 * (correct_ch3 / (len(sliced) / 3)),
            len(sliced) / 3))

        time.sleep(0.2)
        # os.remove(test_file)

    com.kill()


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

    # spi_demo()
