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


# USING_CH347_I2C = True
#
#
# class TCA9554:
#
#     def __init__(self, i2c_bus_path: str = "/dev/i2c-2", addr: int = 0x74, ch347_dev: CH347HIDDev = None):
#         """
#         initialize a control interface for TCA9554 8-bit I/O extension chip
#         :param i2c_bus_path: str, target i2c bus path, example: "/dev/i2c-2"
#         :param addr: int, 7-bit chip address
#         :param ch347_dev: CH347 Device Class
#         """
#         self.interface_fd = wpi.wiringPiI2CSetupInterface(i2c_bus_path, addr)
#         self.addr = addr
#         self.ch347 = ch347_dev
#
#     def reset_address(self, addr: int):
#         self.interface_fd = wpi.wiringPiI2CSetupInterface("/dev/i2c-2", addr)
#         self.addr = addr
#
#     def set_pin_mode(self, mode: int):
#         """
#         setup input/output mode for 8 pins within one byte, 0b00000000 means all 8 pins is configured as output mode
#         :param mode: int
#         :return:
#         """
#         if USING_CH347_I2C:
#             self.ch347.i2c_write(self.addr, b"\x02" + mode.to_bytes(1))
#         else:
#             wpi.wiringPiI2CWriteReg8(self.interface_fd, 0x02, mode)
#
#     def set_pin_polarity(self, polar: int):
#         """
#         setup input/output polarity for 8 pins within one byte, 0x00 means all 8 pins is configured as non-inverted
#         :param polar: int
#         :return:
#         """
#         if USING_CH347_I2C:
#             self.ch347.i2c_write(self.addr, b"\x02" + polar.to_bytes(1))
#         else:
#             wpi.wiringPiI2CWriteReg8(self.interface_fd, 0x02, polar)
#
#     def write_pins(self, value: int):
#         """
#         write specific value to output pin register
#         :param value: int
#         :return:
#         """
#         if USING_CH347_I2C:
#             self.ch347.i2c_write(self.addr, b"\x03" + value.to_bytes(1))
#         else:
#             wpi.wiringPiI2CWriteReg8(self.interface_fd, 0x03, value)
#
#     def read_output_pins(self) -> int:
#         """
#         read current output pin register
#         :return: int
#         """
#         if USING_CH347_I2C:
#             ret = int().from_bytes(self.ch347.i2c_read(self.addr, register_addr=0x03, read_length=1)[1])
#         else:
#             ret = wpi.wiringPiI2CReadReg8(self.interface_fd, 0x03)
#         return ret
#
#     def read_input_pins(self) -> int:
#         """
#         read current input pin register
#         :return: int
#         """
#         if USING_CH347_I2C:
#             ret = int().from_bytes(self.ch347.i2c_read(self.addr, register_addr=0x03, read_length=1)[1])
#         else:
#             ret = wpi.wiringPiI2CReadReg8(self.interface_fd, 0x03)
#         return ret
#
#
# class TCA9539:
#
#     def __init__(self, i2c_bus_path: str = "/dev/i2c-2", addr: int = 0x21, ch347_dev: CH347HIDDev = None):
#         """
#         initialize a control interface for TCA9559 16-bit I/O extension chip
#         :param i2c_bus_path: str, target i2c bus path, example: "/dev/i2c-2"
#         :param addr: int, 7-bit chip address
#         :param ch347_dev: CH347 Device Class
#         """
#         self.interface_fd = wpi.wiringPiI2CSetupInterface(i2c_bus_path, addr)
#         self.addr = addr
#         self.ch347 = ch347_dev
#
#     def reset_address(self, addr: int):
#         self.interface_fd = wpi.wiringPiI2CSetupInterface("/dev/i2c-2", addr)
#         self.addr = addr
#
#     def set_pin_mode(self, mode: int):
#         """
#         setup input/output mode for 16 pins within two byte, 0x0000 means all 16 pins is configured as output mode
#         :param mode: int, 16-bit
#         :return:
#         """
#         if USING_CH347_I2C:
#             self.ch347.i2c_write(self.addr, b"\x06" + mode.to_bytes(2))
#         else:
#             wpi.wiringPiI2CWriteReg16(self.interface_fd, 0x06, mode)
#
#     def write_pins(self, value: int):
#         """
#         write specific value to output 16-bit pin register
#         :param value: int, 16-bit
#         :return:
#         """
#         if USING_CH347_I2C:
#             self.ch347.i2c_write(self.addr, b"\x02" + value.to_bytes(2))
#         else:
#             wpi.wiringPiI2CWriteReg16(self.interface_fd, 0x02, value)
#
#     def write_pins_p0(self, value: int):
#         """
#         write specific value to output 8-bit pin register for port 0
#         :param value: int, 8-bit
#         :return:
#         """
#         if USING_CH347_I2C:
#             self.ch347.i2c_write(self.addr, b"\x02" + value.to_bytes(1))
#         else:
#             wpi.wiringPiI2CWriteReg8(self.interface_fd, 0x02, value)
#
#     def write_pins_p1(self, value: int):
#         """
#         write specific value to output 8-bit pin register for port 1
#         :param value: int, 8-bit
#         :return:
#         """
#         if USING_CH347_I2C:
#             self.ch347.i2c_write(self.addr, b"\x03" + value.to_bytes(1))
#         else:
#             wpi.wiringPiI2CWriteReg8(self.interface_fd, 0x03, value)
#
#     def set_pin_polarity(self, polar: int):
#         """
#         setup input/output polarity for 16 pins within one byte, 0x0000 means all 16 pins is configured as non-inverted
#         :param polar: int
#         :return:
#         """
#         if USING_CH347_I2C:
#             self.ch347.i2c_write(self.addr, b"\x04" + polar.to_bytes(2))
#         else:
#             wpi.wiringPiI2CWriteReg16(self.interface_fd, 0x04, polar)
#
#     def read_output_pins(self) -> int:
#         """
#         read current 16-bit output pin register
#         :return: int
#         """
#         if USING_CH347_I2C:
#             ret = self.ch347.i2c_read(self.addr, 2, b"\x02")
#         else:
#             ret = wpi.wiringPiI2CReadReg16(self.interface_fd, 0x02)
#         return ret
#
#     def read_input_pins(self) -> int:
#         """
#         read current 16-bit input pin register
#         :return: int
#         """
#         if USING_CH347_I2C:
#             ret = self.ch347.i2c_read(self.addr, 2, b"\x00")
#         else:
#             ret = wpi.wiringPiI2CReadReg16(self.interface_fd, 0x00)
#         return ret
#
#
# class BandWidthCtl:
#
#     def __init__(self, i2c_bus: str, ch1_addr: int, ch2_addr: int, ch3_addr: int):
#         self.__ch1_ctl = TCA9554(i2c_bus, ch1_addr)
#         self.__ch2_ctl = TCA9554(i2c_bus, ch2_addr)
#         self.__ch3_ctl = TCA9554(i2c_bus, ch3_addr)
#
#         self.__ch1_ctl.set_pin_mode(0x00)
#         self.__ch2_ctl.set_pin_mode(0x00)
#         self.__ch3_ctl.set_pin_mode(0x00)
#
#         self.__bw_rate_sheet = {
#             "10K": 0xff,
#             "20K": 0xC0,
#             "闭合": 0x3f
#         }
#
#     def set_bandwidth(self, ch1: str, ch2: str, ch3: str):
#         """
#         set bandwidth of each channel, available values: "20K", "10K", "闭合"
#         :param ch1: str
#         :param ch2: str
#         :param ch3: str
#         :return:
#         """
#         self.__ch1_ctl.write_pins(self.__bw_rate_sheet[ch1])
#         self.__ch2_ctl.write_pins(self.__bw_rate_sheet[ch2])
#         self.__ch3_ctl.write_pins(self.__bw_rate_sheet[ch3])
#
#
# class AmpRateCtl:
#
#     def __init__(self, i2c_bus: str, addr: int):
#         self.__TCA9539 = TCA9539(i2c_bus, addr)
#
#         self.__TCA9539.set_pin_mode(0x0000)
#
#         self.__amp_rate_sheet = {
#             "1": 0b0011,
#             "2": 0b0100,
#             "4": 0b0101,
#             "8": 0b0110,
#             "16": 0b0111,
#             "32": 0b1000,
#             "64": 0b1001,
#             "128": 0b1010
#         }
#
#         self.ch1_amp = "1"
#         self.ch2_amp = "1"
#         self.ch3_amp = "1"
#
#         self.leds = [False, False, False, False]
#
#     def update_changes(self):
#         """
#         calling this method will write current settings into TCA9539
#         :return:
#         """
#         ch1_amp = self.__amp_rate_sheet[self.ch1_amp]
#         ch2_amp = self.__amp_rate_sheet[self.ch2_amp]
#         ch3_amp = self.__amp_rate_sheet[self.ch3_amp]
#         led1 = not self.leds[0]
#         led2 = not self.leds[1]
#         led3 = not self.leds[2]
#         led4 = not self.leds[3]
#
#         frame = [
#             ch1_amp | ch2_amp << 4,
#             ch3_amp | led1 << 4 | led2 << 5 | led3 << 6 | led4 << 7
#         ]
#         frame_digest = int().from_bytes(frame, "little", signed=False)
#
#         self.__TCA9539.write_pins(frame_digest)
#
#     def set_amp_rate(self, amp_ch1: str, amp_ch2: str, amp_ch3: str, update=True):
#         """
#         set amplification rate of each channel, amplification rates: "1", "2", "4", "8", "16", "32", "64", "128"
#         :param update: update immediately
#         :param amp_ch1: str
#         :param amp_ch2: str
#         :param amp_ch3: str
#         :return:
#         """
#         self.ch1_amp = amp_ch1
#         self.ch2_amp = amp_ch2
#         self.ch3_amp = amp_ch3
#
#         if update:
#             self.update_changes()
#
#     def set_LED(self, led1: bool = None, led2: bool = None, led3: bool = None, led4: bool = None, update=True):
#         """
#         turn LED indicator on/off (True/False)
#         :param update: update immediately
#         :param led1: bool
#         :param led2: bool
#         :param led3: bool
#         :param led4: bool
#         :return:
#         """
#         if led1 is None:
#             led1 = self.leds[0]
#
#         if led2 is None:
#             led2 = self.leds[1]
#
#         if led3 is None:
#             led3 = self.leds[2]
#
#         if led4 is None:
#             led4 = self.leds[3]
#
#         self.leds[0] = led1
#         self.leds[1] = led2
#         self.leds[2] = led3
#         self.leds[3] = led4
#
#         if update:
#             self.update_changes()
#
#
# class FPGAStatusStruct(BaseModel):
#     sdram_init_done: bool = False
#     spi_data_ready: bool = False
#     spi_rd_error: bool = False
#     sdram_overlap: bool = False
#
#
# class FPGAStat:
#
#     def __init__(self, i2c_bus_path: str, addr: int = 0x40, debug: bool = True):
#         """
#         initialize a status interface for GTEM FPGA designed by Dr.Li
#         :param i2c_bus_path: str, target i2c bus path, example: "/dev/i2c-2"
#         :param addr: int, 7-bit chip address
#         :param debug: bool, enable debug
#         """
#         self.interface_fd = wpi.wiringPiI2CSetupInterface(i2c_bus_path, addr)
#
#         self.flag_debug = debug
#         self.flag_reset = True
#
#         self.cr_cnv_sly_cnt = 2
#         self.cr_cnv_800k_cnt = 125
#
#         self.stat_sdram_overlap = False
#         self.stat_spi_rd_error = False
#         self.stat_spi_data_ready = False
#         self.stat_sdram_init_done = False
#
#     def __send_command(self):
#         """
#         private command update method
#         :return:
#         """
#         # write status
#         payload = [self.flag_reset << 7 | self.flag_debug << 6 | self.cr_cnv_sly_cnt,
#                    self.cr_cnv_800k_cnt,
#                    0x00]
#
#         if self.flag_debug:
#             print("command:", bytes(payload).hex())
#
#         reg = payload[0]
#         payload = int().from_bytes(payload[1:], "little", signed=False)
#
#         wpi.wiringPiI2CWriteReg16(self.interface_fd, reg, payload)
#
#     def read_status(self) -> FPGAStatusStruct:
#         """
#         read fpga status
#         :return: FPGAStatusStruct
#         """
#         # read status
#         # data = [wpi.wiringPiI2CRead(self.interface_fd) for ele in range(3)]
#         reg = self.flag_reset << 7 | self.flag_debug << 6 | self.cr_cnv_sly_cnt
#         data = wpi.wiringPiI2CReadReg16(self.interface_fd, reg)
#
#         if self.flag_debug:
#             print(data)
#
#         self.stat_sdram_init_done = bool(data & 0b00000001)
#         self.stat_spi_data_ready = bool(data & 0b00000010)
#         self.stat_spi_rd_error = bool(data & 0b00000100)
#         self.stat_sdram_overlap = bool(data & 0b00001000)
#
#         ret = FPGAStatusStruct()
#         ret.spi_rd_error = self.stat_spi_rd_error
#         ret.sdram_overlap = self.stat_sdram_overlap
#         ret.sdram_init_done = self.stat_sdram_init_done
#         ret.spi_data_ready = self.stat_spi_data_ready
#
#         return ret
#
#     def reset(self):
#         """
#         reset FPGA
#         :return:
#         """
#
#         self.flag_reset = False  # hold reset flag
#         self.__send_command()
#         self.flag_reset = True  # release reset flag
#         self.__send_command()
#
#     def enable_debug(self, enable=True):
#         """
#         enable/disable debug
#         :param enable: bool
#         :return:
#         """
#         self.flag_debug = enable
#         self.__send_command()
#
#     def set_cnv_settings(self, cnv_sly_cnt=2, cnv_800k_cnt=125):
#         """
#         set cnv settings
#         :param cnv_sly_cnt: int, default: 2, this value determine duration of cnv, counted by pll_clk
#         :param cnv_800k_cnt: int, default: 125, cnt value when in 800k clock speed. e.g. set this value to 100M/800K=125
#         when pll_clk = 100M, sample rate of ADC is 800K.
#         :return:
#         """
#         self.cr_cnv_800k_cnt = cnv_800k_cnt
#         self.cr_cnv_sly_cnt = cnv_sly_cnt
#         self.__send_command()
#
#
# class FPGACtl:
#
#     def __init__(self, i2c_bus_path: str, addr: int = 0x30, debug: bool = False):
#         """
#         initialize a control interface for GTEM FPGA designed by Dr. Li
#         :param i2c_bus_path: str, target i2c bus path, example: "/dev/i2c-2"
#         :param addr: int, 7-bit chip address
#         """
#         self.interface_fd = wpi.wiringPiI2CSetupInterface(i2c_bus_path, addr)
#         self.fpga_is_open = False
#         self.chn_is_open = [False, False, False]
#         # 0--500 1--1k 2--2k 3--4k 4--8k 5--10k 6--20k 7--32k
#         # 8--40k 9--80k A--25k B--50k C--100k D--200k E--400k F--800k
#         self.sample_rate_level = 0x0d
#         # 0-16
#         self.chn_amp_rate_level = [0, 0, 0]
#
#         self.__amp_rate_sheet = {
#             "1": 0b0011,
#             "2": 0b0100,
#             "4": 0b0101,
#             "8": 0b0110,
#             "16": 0b0111,
#             "32": 0b1000,
#             "64": 0b1001,
#             "128": 0b1010
#         }
#
#         self.debug = debug
#
#     def __send_command(self):
#         """
#         private command update method
#         :return:
#         """
#         if self.fpga_is_open:
#             fpga_status = 0xa0
#         else:
#             fpga_status = 0x50
#
#         payload = [fpga_status | (self.chn_is_open[0] | self.chn_is_open[1] << 1 | self.chn_is_open[2] << 2),
#                    (self.sample_rate_level % 16 << 4) | (self.chn_amp_rate_level[0] % 16),
#                    (self.chn_amp_rate_level[1] % 16 << 4) | (self.chn_amp_rate_level[2] % 16)]
#
#         if self.debug:
#             print("command:", bytes(payload).hex())
#
#         reg = payload[0]
#         payload = int().from_bytes(payload[1:], "little", signed=False)
#
#         wpi.wiringPiI2CWriteReg16(self.interface_fd, reg, payload)
#
#     def start_FPGA(self):
#         """
#         start FPGA transmission
#         :return:
#         """
#         self.fpga_is_open = True
#
#         self.__send_command()
#
#     def stop_FPGA(self):
#         """
#         stop FPGA transmission
#         :return:
#         """
#         self.fpga_is_open = False
#
#         self.__send_command()
#
#     def enable_channels(self, ch1: bool = True, ch2: bool = True, ch3: bool = True):
#         """
#         set each channel's status (True: start / False: stop)
#         :param ch1: bool
#         :param ch2: bool
#         :param ch3: bool
#         :return:
#         """
#         self.chn_is_open[2] = ch1
#         self.chn_is_open[1] = ch2
#         self.chn_is_open[0] = ch3
#
#         # if self.debug:
#         #     self.__send_command()
#
#     def set_sample_rate_level(self, sample_rate_level):
#         """
#         set sample rate level,
#         0--500  1--1k   2--2k   3--4k   4--8k   5--10k  6--20k  7--32k
#         8--40k  9--80k  A--25k  B--50k  C--100k D--200k E--400k F--800k
#         :param sample_rate_level: int
#         :return:
#         """
#         self.sample_rate_level = sample_rate_level
#
#         # if self.debug:
#         #     self.__send_command()
#
#     def set_amp_rate_of_channels(self, ch1_amp: str, ch2_amp: str, ch3_amp: str):
#         """
#         set the amplification rate of each channel, transformed by transforming dict
#         :param ch1_amp: str
#         :param ch2_amp: str
#         :param ch3_amp: str
#         :return:
#         """
#         self.chn_amp_rate_level[0] = self.__amp_rate_sheet[ch1_amp]
#         self.chn_amp_rate_level[1] = self.__amp_rate_sheet[ch2_amp]
#         self.chn_amp_rate_level[2] = self.__amp_rate_sheet[ch3_amp]
#
#         # if self.debug:
#         #     self.__send_command()


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
                                             "sdram_overlap": False
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

            # while self.mp_status["live"]:
            #     status = self.fpga_stat.read_status()
            #     self.mp_status['status'] = status.dict()
            #
            #     if status.spi_data_ready:
            #         break
            #     else:
            #         time.sleep(0.001)

            time.sleep(1)

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

    def get_status(self) -> FPGAStatusStruct:
        ret = FPGAStatusStruct.parse_obj(self.mp_status['status'])

        return ret

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
