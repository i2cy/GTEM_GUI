#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: spi
# Created on: 2022/11/22

from ch347api import CH347HIDDev
from ch347api import VENDOR_ID, PRODUCT_ID
import struct
import numpy as np
import time
from queue import Empty, Full
from multiprocessing import Process, Queue, Manager

if __name__ == "__main__":
    from i2c import FPGACtl, FPGAStat, FPGAStatusStruct
else:
    from .i2c import FPGACtl, FPGAStat, FPGAStatusStruct


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


SPI_DEV = (1, 0)
MAX_FREQ = 48_000_000
BITS_PER_WORD = 8
SPI_MODE = 0b00

DATA_FRAME_SIZE = 3 * 4


class FPGACom:

    def __init__(self, to_file_only: bool = False, debug=True):

        self.to_file_only = to_file_only
        self.mp_status = Manager().dict({"live": True,
                                         "running": False,
                                         "file_lock": False,
                                         "filename": "",
                                         "debug": debug,
                                         "swapping_file": False,
                                         "batch_size": 200_000,
                                         "status": {
                                             "sdram_init_done": False,
                                             "spi_data_ready": False,
                                             "spi_rd_error": False,
                                             "sdram_overlap": False,
                                             "pll_ready": False
                                         }})

        self.mp_raw_data_queue = Queue(200_000_000)
        self.mp_ch1_data_queue_x4 = Queue(200_000_000 // 4)
        self.mp_ch2_data_queue_x4 = Queue(200_000_000 // 4)
        self.mp_ch3_data_queue_x4 = Queue(200_000_000 // 4)

        self.spi_dev = None

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

    def set_batch_size(self, sample_rate_level: int):
        """
        0--500  1--1k   2--2k   3--4k   4--8k   5--10k  6--20k  7--32k
        8--40k  9--80k  A--25k  B--50k  C--100k D--200k E--400k F--800k
        """
        __comvert_list = (500, 1_000, 2_000, 4_000, 8_000, 10_000, 20_000, 32_000,
                          40_000, 80_000, 25_000, 50_000, 100_000, 200_000, 400_000, 800_000)
        self.mp_status['batch_size'] = __comvert_list[sample_rate_level]

    def proc_spi_receiver(self):
        # initialize CH347 communication interface
        self.spi_dev = CH347HIDDev(VENDOR_ID, PRODUCT_ID, 1)
        self.spi_dev.init_SPI(clock_speed_level=3, mode=3)

        # initialize FPGA status report
        # fpga_stat = FPGAStat("/dev/i2c-2", self.mp_status['debug'])
        # fpga_stat.enable_debug(True)

        if self.mp_status["debug"]:
            print("proc_spi_receiver started")

        while self.mp_status["live"]:
            if not self.mp_status["running"]:  # 待机状态
                time.sleep(0.001)
                continue

            if self.mp_status['status']['spi_data_ready']:
                self.mp_status['status']['spi_data_ready'] = False
                if self.mp_status['debug']:
                    print("spi data ready detected")
            else:
                time.sleep(0.001)
                continue

            try:
                frame_size = 32768 // 2
                data = []
                first = True
                self.spi_dev.set_CS1()
                for i in range(self.mp_status['batch_size'] * DATA_FRAME_SIZE // frame_size):
                    if first:
                        first = False
                        # self.spi_dev.spi_write(b"\xff")
                    data.extend(self.spi_dev.spi_read(frame_size))
                    if not self.mp_status["running"]:
                        break
                if self.mp_status["running"]:
                    data.extend(self.spi_dev.spi_read(self.mp_status['batch_size'] * DATA_FRAME_SIZE % frame_size))
                self.spi_dev.set_CS1(False)
                print("received data of total length: {}".format(len(data)))
                print("first 3 frame: \n{}\n{}\n{}".format(
                    bytes(data[0:12]).hex(), bytes(data[12:24]).hex(), bytes(data[24:36]).hex()
                ))

                try:
                    self.mp_raw_data_queue.put(data)
                except Full:
                    continue

            except Exception as err:
                print("[error] spi receiver error, {}".format(err))
                continue

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

            dt = np.dtype(np.uint32)
            dt.newbyteorder(">")

            frame = np.frombuffer(byte_array, dtype=dt)

            # print("1", hex(frame[0]))

            frame = np.array([int().from_bytes(
                int(ele).to_bytes(4, "little", signed=False)[1:4],
                "big", signed=True
            ) for ele in frame], dtype=np.int32)
            # print("2", hex(frame[0]))

            frame = (frame / 8_388_607) * 4096

            # print("3", np.max(frame), "mv")

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
                    # t_debug = time.time()

                    time.sleep(0.002)

                    ch1_batch.clear()
                    ch2_batch.clear()
                    ch3_batch.clear()
                    cnt = 0

        if self.mp_status["debug"]:
            print("proc_data_process stopped")

    def update_status(self, status: FPGAStatusStruct):
        self.mp_status["status"]["sdram_init_done"] = status.sdram_init_done
        self.mp_status["status"]["spi_data_ready"] = status.spi_data_ready
        self.mp_status["status"]["spi_rd_error"] = status.spi_rd_error
        self.mp_status["status"]["sdram_overlap"] = status.sdram_overlap
        self.mp_status["status"]["pll_ready"] = status.pll_ready

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


if __name__ == '__main__':
    import wiringpi as wpi

    wpi.wiringPiSPISetup(0, 500000)
