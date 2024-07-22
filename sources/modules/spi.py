#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: spi
# Created on: 2022/11/22

from ctypes import c_bool, c_int, c_char_p
from ch347api import CH347HIDDev, SPIClockFreq, SPIDevice
from ch347api import VENDOR_ID, PRODUCT_ID
import struct
import numpy as np
import time
from queue import Empty, Full
from multiprocessing import Process, Queue, Manager, Value, Array
import warnings
import threading

if __name__ == "__main__":
    from i2c import FPGACtl, FPGAStatusStruct
else:
    from .i2c import FPGACtl, FPGAStatusStruct

SPI_SPEED = SPIClockFreq.f_30M

SPI_MODE = 0


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


class FPGACom:

    def __init__(self, to_file_only: bool = False, ctl: FPGACtl = None, debug=True):

        self.to_file_only = to_file_only
        # self.mp_manager = Manager()
        # self.mp_status = self.mp_manager.dict({"live": True,
        #                                  "running": False,
        #                                  "file_lock": False,
        #                                  "filename": "",
        #                                  "debug": debug,
        #                                  "swapping_file": False,
        #                                  "batch_size": 200_000})

        self.mp_live = Value(c_bool, True)
        self.mp_running = Value(c_bool, False)
        self.mp_debug = Value(c_bool, debug)
        self.mp_filelock = Value(c_bool, False)
        self.mp_swapping_file = Value(c_bool, False)
        self.mp_batchsize = Value(c_int, 200_000)
        self.mp_set_filename = Queue(1024)

        self.stat_main2sub_sdram_init_done = Queue(1024)
        self.stat_main2sub_spi_data_ready = Queue(1024)
        self.stat_main2sub_spi_rd_error = Queue(1024)
        self.stat_main2sub_sdram_overlap = Queue(1024)
        self.stat_main2sub_pll_ready = Queue(1024)

        self.stat_sub2main_read_start = Queue(1024)
        self.stat_sub2main_read_done = Queue(1024)
        self.flag_spi_reading = False

        self.mp_raw_data_queue = Queue(200_000_000)
        self.mp_ch1_data_queue_x4 = Queue(200_000_000 // 4)
        self.mp_ch2_data_queue_x4 = Queue(200_000_000 // 4)
        self.mp_ch3_data_queue_x4 = Queue(200_000_000 // 4)

        self.output_filename = ""

        self.spi_dev = None
        if ctl is None:
            ctl = FPGACtl("/dev/i2c-2")
        self.ctl = ctl

        self.filename = ""
        self.file_io = None

        self.processes = []
        self.threads = []

    def __del__(self):
        self.kill()

    def set_output_file(self, filename):
        self.output_filename = filename
        if self.mp_filelock.value:
            print("swapping file")
            self.mp_swapping_file.value = True
            self.mp_set_filename.put(self.output_filename)
            while self.mp_swapping_file.value:
                time.sleep(0.001)
            print("swapping file completed")

    def set_batch_size(self, sample_rate_level: int):
        """
        0--500  1--1k   2--2k   3--4k   4--8k   5--10k  6--20k  7--32k
        8--40k  9--80k  A--25k  B--50k  C--100k D--200k E--400k F--800k
        """
        __comvert_list = (2048 * 2, 4096 * 2, 8192 * 2, 16384 * 2, 32768 * 2, 32768 * 2, 65536 * 2, 131072 * 2,
                          131072 * 2, 262144 * 2, 65536 * 2, 524288 * 2, 1048576 * 2, 2097152 * 2, 4194304 * 2,
                          8388608 * 2)
        self.mp_batchsize.value = __comvert_list[sample_rate_level]

    def thr_status_update_thread(self):
        if self.mp_debug.value:
            print("\nstatus_update_thread started")

        while self.mp_live.value:

            if not self.mp_running.value:
                # wait for start signal
                self.flag_spi_reading = False
                time.sleep(0.002)
                continue

            self.ctl.stat_spi_data_ready = False
            self.ctl.stat_pll_ready = False
            self.ctl.stat_spi_rd_error = False
            self.ctl.stat_sdram_overlap = False
            self.ctl.stat_sdram_init_done = False

            if self.flag_spi_reading:
                try:
                    read_done = self.stat_sub2main_read_done.get(timeout=0.005)
                except Empty:
                    read_done = False
                self.flag_spi_reading = not read_done
            else:
                try:
                    read_start = self.stat_sub2main_read_start.get(timeout=0.005)
                except Empty:
                    read_start = False
                self.flag_spi_reading = read_start

            if not self.flag_spi_reading:
                status = self.ctl.read_status()
                self.update_status(status)
                if status.spi_data_ready:
                    self.flag_spi_reading = True
                if self.mp_debug.value:
                    if status.sdram_overlap:
                        warnings.warn("SD RAM overlap detected")
                    if status.spi_rd_error:
                        warnings.warn("Read error detected")

        if self.mp_debug.value:
            print("\nstatus_update_thread stopped")

        return

    def proc_spi_receiver(self):
        # initialize CH347 communication interface
        self.spi_dev = CH347HIDDev(VENDOR_ID, PRODUCT_ID, 1)
        self.spi_dev.init_SPI(clock_freq_level=SPI_SPEED, mode=SPI_MODE)

        # initialize FPGA status report
        # fpga_stat = FPGAStat("/dev/i2c-2", self.mp_debug.value)
        # fpga_stat.enable_debug(True)

        if self.mp_debug.value:
            print("\nproc_spi_receiver started")

        first = False

        while self.mp_live.value:
            if not self.mp_running.value:  # 待机状态
                time.sleep(0.001)
                first = True
                continue

            try:
                data_ready = self.stat_main2sub_spi_data_ready.get(timeout=0.5)
            except Empty:
                data_ready = False

            if data_ready:
                if self.mp_debug.value:
                    print("\nspi data ready detected")
            else:
                continue

            try:
                frame_size = 32756
                data = []
                self.spi_dev.set_CS1()
                read_byte_count = 0
                batch = self.mp_batchsize.value
                for i in range(batch // frame_size):
                    # if first:
                    #     first = False
                    #     read = self.spi_dev.spi_read(frame_size + 2)
                    #     print("CS header: 0x{}".format(bytes(read[0:2])))
                    #     # self.spi_dev.spi_write(b"\xaa\xaa")
                    #
                    #     read = read[2:]
                    # else:
                    #     read = self.spi_dev.spi_read(frame_size)
                    read = self.spi_dev.spi_read(frame_size)
                    read_byte_count += frame_size
                    data.extend(read)
                    if not self.mp_running.value:
                        break
                if batch > read_byte_count and self.mp_running.value:
                    if first:
                        first = False
                        read = self.spi_dev.spi_read(batch - read_byte_count + 2)
                        print("CS header: 0x{}".format(bytes(read[0:2])))
                        # self.spi_dev.spi_write(b"\xaa\xaa")

                        read = read[2:]
                    else:
                        read = self.spi_dev.spi_read(batch - read_byte_count)
                    data.extend(read)

                self.spi_dev.set_CS1(False)
                # print("received data of total length: {}".format(len(data)))
                # print("first 3 frame: \n{}\n{}\n{}".format(
                #     bytes(data[0:12]).hex(), bytes(data[12:24]).hex(), bytes(data[24:36]).hex()
                # ))

                try:
                    self.mp_raw_data_queue.put(data)
                except Full:
                    continue

            except Exception as err:
                print("[error] spi receiver error, {}".format(err))
                continue

            self.stat_sub2main_read_done.put(True)

        self.spi_dev.reset()

        if self.mp_debug.value:
            print("\nproc_spi_receiver stopped")

        return

    def proc_data_process(self):
        ch1_batch = []
        ch2_batch = []
        ch3_batch = []
        cnt = 0

        file_closed = True
        file_io = None

        if self.mp_debug.value:
            print("\nproc_data_process started")

        t_debug = time.time()
        filename = ""
        # calculate channel info bytes
        ch_addon = [
            (self.ctl.mp_ch1_amp_rate.value % 16) << 4 | self.ctl.ch1_is_open.value << 2 | 1,
            (self.ctl.mp_ch2_amp_rate.value % 16) << 4 | self.ctl.ch2_is_open.value << 2 | 1,
            (self.ctl.mp_ch3_amp_rate.value % 16) << 4 | self.ctl.ch3_is_open.value << 2 | 1
        ]

        while self.mp_live.value:
            if not self.mp_running.value:  # 待机状态
                if not file_closed:
                    file_io.close()
                    file_closed = True
                    self.mp_filelock.value = False
                    print("proc_data_process file closed")
                    time.sleep(0.001)
                continue

            if file_closed:
                while self.mp_live.value:
                    try:
                        filename = self.mp_set_filename.get(timeout=0.5)
                        print("set spi filename:", filename)

                        break
                    except Empty:
                        continue

                file_io = open(filename, "wb")
                file_closed = False
                self.mp_filelock.value = True
                print("\nproc_data_process file opened")

            try:
                frame = self.mp_raw_data_queue.get(timeout=0.5)
            except Empty:
                continue

            if not len(frame):
                continue

            byte_array = bytes(frame)

            if self.mp_swapping_file.value:
                # swapping file (which means they have started a new data retrieve command)
                while self.mp_live.value:
                    try:
                        filename = self.mp_set_filename.get(timeout=0.5)
                        print("set spi filename:", filename)
                        break
                    except Empty:
                        continue
                file_io.close()
                file_io = open(filename, "wb")
                self.mp_swapping_file.value = False
                # calculate channel info bytes
                ch_addon = [
                    (self.ctl.mp_ch1_amp_rate.value % 16) << 4 | self.ctl.ch1_is_open.value << 2 | 1,
                    (self.ctl.mp_ch2_amp_rate.value % 16) << 4 | self.ctl.ch2_is_open.value << 2 | 1,
                    (self.ctl.mp_ch3_amp_rate.value % 16) << 4 | self.ctl.ch3_is_open.value << 2 | 1
                ]

            # TODO: make sure channel addon bytes wrote into the file
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

        if self.mp_debug.value:
            print("\nproc_data_process stopped")

        return

    def update_status(self, status: FPGAStatusStruct):
        # if status.sdram_init_done:
        #     self.stat_main2sub_sdram_init_done.put(True, block=False)
        if status.spi_data_ready:
            self.stat_main2sub_spi_data_ready.put(True, block=False)
        # if status.spi_rd_error:
        #     self.stat_main2sub_spi_rd_error.put(True, block=False)
        # if status.sdram_overlap:
        #     self.stat_main2sub_sdram_overlap.put(True, block=False)
        # if status.pll_ready:
        #     self.stat_main2sub_pll_ready.put(True, block=False)

    def start(self):
        self.mp_live.value = True  # start signal

        self.processes.append(Process(target=self.proc_spi_receiver, daemon=True))
        self.processes.append(Process(target=self.proc_data_process, daemon=True))

        [ele.start() for ele in self.processes]

        self.ctl.reset()

        self.threads.append(threading.Thread(target=self.thr_status_update_thread, daemon=True))
        [ele.start() for ele in self.threads]

    def debug(self, value: bool = True):
        self.mp_debug.value = value

    def kill(self):
        self.close()
        while self.mp_live.value:
            self.mp_live.value = False  # stop signal

        time.sleep(0.2)
        [ele.join() for ele in self.threads]
        [ele.join() for ele in self.processes]
        [ele.terminate() for ele in self.processes]
        time.sleep(0.2)
        self.processes.clear()
        self.threads.clear()

        if self.mp_debug.value:
            print("killed all subprocesses")

    def open(self):
        if not self.ctl.fpga_is_open:
            self.ctl.stat_pll_ready = False
            self.ctl.stat_sdram_overlap = False
            self.ctl.stat_spi_data_ready = False
            self.ctl.stat_spi_rd_error = False
            self.ctl.stat_sdram_init_done = False
            self.ctl.start_FPGA()

        self.mp_running.value = True
        self.mp_set_filename.put(self.output_filename)
        while not self.mp_filelock.value:
            time.sleep(0.001)

    def close(self):
        try:
            while self.mp_running.value:
                self.mp_running.value = False
        except Exception as err:
            print("error while exiting FPGA-COM object,", err)
        t0 = time.time()
        while self.mp_filelock.value and time.time() - t0 < 5:
            time.sleep(0.001)

        if self.ctl.fpga_is_open:
            self.ctl.stop_FPGA()


if __name__ == '__main__':
    import wiringpi as wpi

    wpi.wiringPiSPISetup(0, 500000)
