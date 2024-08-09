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

        # initialize
        self.to_file_only = to_file_only  # flag disables x4 queues
        self.flag_spi_reading = False  # flag indicates receiver is reading data from SPI

        self.mp_live = Value(c_bool, True)  # life signal for processes
        self.mp_running = Value(c_bool, False)  # IDLE signal (True - Running, False - IDLE)
        self.mp_debug = Value(c_bool, debug)  # debug flag
        self.mp_filelock = Value(c_bool, False)  # file in use flag
        self.mp_swapping_file = Value(c_bool, False)  # signal for swapping filename
        self.mp_batchsize = Value(c_int, 200_000)  # batch size of data (corresponding to sample rate)
        self.mp_set_filename = Queue(1024)  # queue for filename setting

        # signal queues
        self.stat_main2sub_sdram_init_done = Queue(1024)
        self.stat_main2sub_spi_data_ready = Queue(1024)
        self.stat_main2sub_spi_rd_error = Queue(1024)
        self.stat_main2sub_sdram_overlap = Queue(1024)
        self.stat_main2sub_pll_ready = Queue(1024)

        self.stat_sub2main_read_done = Queue(1024)

        # data queues
        self.mp_raw_data_queue = Queue(200_000_000)
        self.mp_ch1_data_queue_x4 = Queue(200_000_000 // 4)
        self.mp_ch2_data_queue_x4 = Queue(200_000_000 // 4)
        self.mp_ch3_data_queue_x4 = Queue(200_000_000 // 4)

        # initialize SPI Device and FPGACtl object
        self.spi_dev = None
        if ctl is None:
            ctl = FPGACtl("/dev/i2c-2")
        self.ctl = ctl

        # filename cache
        self.output_filename = ""

        # processes and threads indicator
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
        __convert_list = (2048, 4096, 8192, 16384, 32768, 32768, 65536, 131072,
                          131072, 262144, 65536, 131072, 262144, 524288, 1048576, 2097152)

        self.mp_batchsize.value = __convert_list[sample_rate_level] * 2

    def thr_status_update_thread(self):
        if self.mp_debug.value:
            print("\nstatus_update_thread started, ts: {:.1f}".format(time.time()))

        while self.mp_live.value:
            # while IDLE
            if not self.mp_running.value:
                # wait for start signal
                self.flag_spi_reading = False
                time.sleep(0.005)
                continue

            # reset all flags of status
            self.ctl.stat_spi_data_ready = False
            self.ctl.stat_pll_ready = False
            self.ctl.stat_spi_rd_error = False
            self.ctl.stat_sdram_overlap = False
            self.ctl.stat_sdram_init_done = False

            # while spi receiver is reading
            if self.flag_spi_reading:
                # try to get read-done signal from spi receiver
                try:
                    read_done = self.stat_sub2main_read_done.get(timeout=0.005)
                except Empty:
                    read_done = False
                self.flag_spi_reading = not read_done

            # while spi receiver stopped reading
            else:
                # read FPGA status if spi receiver is not reading
                status = self.ctl.read_status()
                # update status flags to multithreading queue
                self.update_status(status)
                # assume that spi receiver is reading after received spi_data_ready flag
                if status.spi_data_ready:
                    self.flag_spi_reading = True
                # debug output
                if status.sdram_overlap:
                    warnings.warn("SD RAM overlap detected, ts: {:.1f}".format(time.time()))
                if status.spi_rd_error:
                    warnings.warn("Read error detected, ts: {:.1f}".format(time.time()))

        # closing procedure
        self.stat_sub2main_read_done.close()
        self.stat_main2sub_spi_data_ready.close()
        self.stat_main2sub_spi_rd_error.close()
        self.stat_main2sub_sdram_overlap.close()
        self.stat_main2sub_pll_ready.close()

        if self.mp_debug.value:
            print("\nstatus_update_thread stopped, ts: {:.1f}".format(time.time()))

        return

    def proc_spi_receiver(self):
        # debug output
        if self.mp_debug.value:
            print("\nproc_spi_receiver started, ts: {:.1f}".format(time.time()))

        # initialize CH347 communication interface
        self.spi_dev = CH347HIDDev(VENDOR_ID, PRODUCT_ID, 1)
        self.spi_dev.init_SPI(clock_freq_level=SPI_SPEED, mode=SPI_MODE)

        # locals
        frame_size = 32756

        # receiver process loop
        while self.mp_live.value:
            # while IDLE
            if not self.mp_running.value:
                time.sleep(0.005)
                continue

            # get spi_data_ready flag from FPGACtl
            try:
                data_ready = self.stat_main2sub_spi_data_ready.get(timeout=0.5)
            except Empty:
                data_ready = False

            # wait to spi_data_ready to continue
            if data_ready:
                print("\rspi data ready detected, ts: {:.1f}".format(time.time()), end="")
            else:
                continue

            # try to read one small batch of data from FPGA using SPI
            try:
                # initialize cache list
                data = []
                # initialize miscellaneous
                read_byte_count = 0
                # enable SPI CS
                self.spi_dev.set_CS1()
                # get size of batch from multithreading Value
                batch = self.mp_batchsize.value
                # read data 32756 bytes each time
                for i in range(batch // frame_size):
                    read = self.spi_dev.spi_read(frame_size)
                    read_byte_count += frame_size
                    data.extend(read)
                    if not self.mp_running.value:
                        break
                # read remaining data
                if batch > read_byte_count and self.mp_running.value:
                    read = self.spi_dev.spi_read(batch - read_byte_count)
                    data.extend(read)
                # disable SPI CS
                self.spi_dev.set_CS1(False)
                # put data in raw_data_queue for proc_data_process to use
                try:
                    self.mp_raw_data_queue.put(data)
                except Full:
                    warnings.warn("mp_raw_data_queue full, ts: {:.1f}".format(time.time()))

            except Exception as err:
                warnings.warn("[error] spi receiver error, {}, ts: {:.1f}".format(err, time.time()))

            # inform thr_status_update_thread that receiver has done reading
            self.stat_sub2main_read_done.put(True)

        # closing procedure
        self.stat_sub2main_read_done.close()
        self.spi_dev.reset()

        if self.mp_debug.value:
            print("\nproc_spi_receiver stopped, ts: {:.1f}".format(time.time()))

        return

    def proc_data_process(self):
        # debug output
        if self.mp_debug.value:
            print("\nproc_data_process started, ts: {:.1f}".format(time.time()))

        # initialize cache list (A/B list), and swap flag
        ch1_batch_a = []
        ch2_batch_a = []
        ch3_batch_a = []
        ch1_batch_b = []
        ch2_batch_b = []
        ch3_batch_b = []
        batch_is_a = True

        # initialize miscellaneous
        ch_addon = [b"\x00"] * 3

        # initialize counter for batch queue
        cnt = 0

        # initialize flag
        file_closed = True

        # preallocate file_io object
        file_io = None

        # data process loop
        while self.mp_live.value:
            # while IDLE
            if not self.mp_running.value:
                if not file_closed:
                    file_io.close()
                    file_closed = True
                    self.mp_filelock.value = False
                    print("proc_data_process file closed, ts: {:.1f}".format(time.time()))
                    time.sleep(0.02)
                continue  # keeps IDLE

            # close file_io to replace existed file_io object with a new one when signal of swapping file received
            if self.mp_swapping_file.value:
                # close file_io object and set file_closed flag to True
                file_io.close()
                file_closed = True
                self.mp_swapping_file.value = False

            # create new file_io object using a new filename got from set_filename queue when file closed
            if file_closed:
                try:
                    filename = self.mp_set_filename.get(timeout=0.5)  # get new filename from queue
                    print("set spi filename:", filename)
                    file_io = open(filename, "wb")  # open new file io object
                    file_closed = False  # set file_closed flag value to False
                    self.mp_filelock.value = True  # enable file object lock
                    print("\nproc_data_process file opened, ts: {:.1f}".format(time.time()))

                    # calculate one byte of each channel
                    ch_addon = [
                        bytes(((self.ctl.mp_ch1_amp_rate.value % 16) << 4 | self.ctl.ch1_is_open.value << 2 | 1), ),
                        bytes(((self.ctl.mp_ch2_amp_rate.value % 16) << 4 | self.ctl.ch2_is_open.value << 2 | 1), ),
                        bytes(((self.ctl.mp_ch3_amp_rate.value % 16) << 4 | self.ctl.ch3_is_open.value << 2 | 1), )
                    ]
                except Empty:
                    continue  # repeat this operation until new file_io has been created and opened

            # get one small batch of data from raw_data_queue
            try:
                frame = self.mp_raw_data_queue.get(timeout=0.5)
                if not len(frame):
                    continue  # make sure the one small batch is not empty
            except Empty:
                continue  # repeat this operation until one small batch data got

            # convert iterable data to byte array
            byte_array = bytes(frame)

            # write data to file with 32-bit per channel (also convert data to numpy array)
            for b_i in range(len(byte_array) // 9):
                b_st = b_i * 9
                # cache data
                ch1 = byte_array[b_st:b_st + 3]
                ch2 = byte_array[b_st + 3:b_st + 6]
                ch3 = byte_array[b_st + 6:b_st + 9]

                # convert bytes to int in batch
                if not self.to_file_only:  # skip this operation if to_file_only is enabled
                    if batch_is_a:
                        ch1_batch_a.append(int.from_bytes(ch1, byteorder="big", signed=True))
                        ch2_batch_a.append(int.from_bytes(ch2, byteorder="big", signed=True))
                        ch3_batch_a.append(int.from_bytes(ch3, byteorder="big", signed=True))
                    else:
                        ch1_batch_b.append(int.from_bytes(ch1, byteorder="big", signed=True))
                        ch2_batch_b.append(int.from_bytes(ch2, byteorder="big", signed=True))
                        ch3_batch_b.append(int.from_bytes(ch3, byteorder="big", signed=True))

                # write data, data structure (big endian): [uint_8 info_byte, int_24 data_payload]
                file_io.write(ch_addon[0] + ch1)  # ch1
                file_io.write(ch_addon[1] + ch2)  # ch2
                file_io.write(ch_addon[2] + ch3)  # ch3

            # put batched data in data_queue_x4
            if not self.to_file_only:
                if cnt < 4:
                    cnt += 1
                else:
                    cnt = 0
                    # put data when 4 small batch is collected
                    if batch_is_a:
                        self.mp_ch1_data_queue_x4.put(ch1_batch_a)
                        self.mp_ch2_data_queue_x4.put(ch2_batch_a)
                        self.mp_ch3_data_queue_x4.put(ch3_batch_a)
                        batch_is_a = False
                        ch1_batch_b.clear()
                        ch2_batch_b.clear()
                        ch3_batch_b.clear()
                    else:
                        self.mp_ch1_data_queue_x4.put(ch1_batch_b)
                        self.mp_ch2_data_queue_x4.put(ch2_batch_b)
                        self.mp_ch3_data_queue_x4.put(ch3_batch_b)
                        batch_is_a = True
                        ch1_batch_a.clear()
                        ch2_batch_a.clear()
                        ch3_batch_a.clear()

        if self.mp_debug.value:
            print("\nproc_data_process stopped, ts: {:.1f}".format(time.time()))

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
