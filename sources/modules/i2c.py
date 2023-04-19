#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: i2c
# Created on: 2022/12/2

import wiringpi as wpi


class TCA9554:

    def __init__(self, i2c_bus_path: str, addr: int = 0x74):
        """
        initialize a control interface for TCA9554 8-bit I/O extension chip
        :param i2c_bus_path: str, target i2c bus path, example: "/dev/i2c-2"
        :param addr: int, 7-bit chip address
        """
        self.interface_fd = wpi.wiringPiI2CSetupInterface(i2c_bus_path, addr)

    def reset_address(self, addr: int):
        self.interface_fd = wpi.wiringPiI2CSetupInterface("/dev/i2c-2", addr)

    def set_pin_mode(self, mode: int):
        """
        setup input/output mode for 8 pins within one byte, 0b00000000 means all 8 pins is configured as output mode
        :param mode: int
        :return:
        """
        wpi.wiringPiI2CWriteReg8(self.interface_fd, 0x02, mode)

    def set_pin_polarity(self, polar: int):
        """
        setup input/output polarity for 8 pins within one byte, 0x00 means all 8 pins is configured as non-inverted
        :param polar: int
        :return:
        """
        wpi.wiringPiI2CWriteReg8(self.interface_fd, 0x02, polar)

    def write_pins(self, value: int):
        """
        write specific value to output pin register
        :param value: int
        :return:
        """
        wpi.wiringPiI2CWriteReg8(self.interface_fd, 0x03, value)

    def read_output_pins(self) -> int:
        """
        read current output pin register
        :return: int
        """
        ret = wpi.wiringPiI2CReadReg8(self.interface_fd, 0x03)
        return ret

    def read_input_pins(self) -> int:
        """
        read current input pin register
        :return: int
        """
        ret = wpi.wiringPiI2CReadReg8(self.interface_fd, 0x03)
        return ret


class TCA9539:

    def __init__(self, i2c_bus_path: str, addr: int = 0x21):
        """
        initialize a control interface for TCA9559 16-bit I/O extension chip
        :param i2c_bus_path: str, target i2c bus path, example: "/dev/i2c-2"
        :param addr: int, 7-bit chip address
        """
        self.interface_fd = wpi.wiringPiI2CSetupInterface(i2c_bus_path, addr)

    def reset_address(self, addr: int):
        self.interface_fd = wpi.wiringPiI2CSetupInterface("/dev/i2c-2", addr)

    def set_pin_mode(self, mode: int):
        """
        setup input/output mode for 16 pins within two byte, 0x0000 means all 16 pins is configured as output mode
        :param mode: int, 16-bit
        :return:
        """
        wpi.wiringPiI2CWriteReg16(self.interface_fd, 0x06, mode)

    def write_pins(self, value: int):
        """
        write specific value to output 16-bit pin register
        :param value: int, 16-bit
        :return:
        """
        wpi.wiringPiI2CWriteReg16(self.interface_fd, 0x02, value)

    def write_pins_p0(self, value: int):
        """
        write specific value to output 8-bit pin register for port 0
        :param value: int, 8-bit
        :return:
        """
        wpi.wiringPiI2CWriteReg8(self.interface_fd, 0x02, value)

    def write_pins_p1(self, value: int):
        """
        write specific value to output 8-bit pin register for port 1
        :param value: int, 8-bit
        :return:
        """
        wpi.wiringPiI2CWriteReg8(self.interface_fd, 0x03, value)

    def set_pin_polarity(self, polar: int):
        """
        setup input/output polarity for 16 pins within one byte, 0x0000 means all 16 pins is configured as non-inverted
        :param polar: int
        :return:
        """
        wpi.wiringPiI2CWriteReg16(self.interface_fd, 0x04, polar)

    def read_output_pins(self) -> int:
        """
        read current 16-bit output pin register
        :return: int
        """
        ret = wpi.wiringPiI2CReadReg16(self.interface_fd, 0x02)
        return ret

    def read_input_pins(self) -> int:
        """
        read current 16-bit input pin register
        :return: int
        """
        ret = wpi.wiringPiI2CReadReg16(self.interface_fd, 0x00)
        return ret


class BandWidthCtl:

    def __init__(self, i2c_bus: str, ch1_addr: int, ch2_addr: int, ch3_addr: int):
        self.__ch1_ctl = TCA9554(i2c_bus, ch1_addr)
        self.__ch2_ctl = TCA9554(i2c_bus, ch2_addr)
        self.__ch3_ctl = TCA9554(i2c_bus, ch3_addr)

        self.__ch1_ctl.set_pin_mode(0x00)
        self.__ch2_ctl.set_pin_mode(0x00)
        self.__ch3_ctl.set_pin_mode(0x00)

        self.__bw_rate_sheet = {
            "10K": 0xff,
            "20K": 0xC0,
            "闭合": 0x3f
        }

    def set_bandwidth(self, ch1: str, ch2: str, ch3: str):
        """
        set bandwidth of each channel, available values: "20K", "10K", "闭合"
        :param ch1: str
        :param ch2: str
        :param ch3: str
        :return:
        """
        self.__ch1_ctl.write_pins(self.__bw_rate_sheet[ch1])
        self.__ch2_ctl.write_pins(self.__bw_rate_sheet[ch2])
        self.__ch3_ctl.write_pins(self.__bw_rate_sheet[ch3])


class AmpRateCtl:

    def __init__(self, i2c_bus: str, addr: int):
        self.__TCA9539 = TCA9539(i2c_bus, addr)

        self.__TCA9539.set_pin_mode(0x0000)

        self.__amp_rate_sheet = {
            "1": 0b0011,
            "2": 0b0100,
            "4": 0b0101,
            "8": 0b0110,
            "16": 0b0111,
            "32": 0b1000,
            "64": 0b1001,
            "128": 0b1010
        }

        self.ch1_amp = "1"
        self.ch2_amp = "1"
        self.ch3_amp = "1"

        self.leds = [False, False, False, False]

    def update_changes(self):
        """
        calling this method will write current settings into TCA9539
        :return:
        """
        ch1_amp = self.__amp_rate_sheet[self.ch1_amp]
        ch2_amp = self.__amp_rate_sheet[self.ch2_amp]
        ch3_amp = self.__amp_rate_sheet[self.ch3_amp]
        led1 = not self.leds[0]
        led2 = not self.leds[1]
        led3 = not self.leds[2]
        led4 = not self.leds[3]

        frame = [
            ch1_amp | ch2_amp << 4,
            ch3_amp | led1 << 4 | led2 << 5 | led3 << 6 | led4 << 7
        ]
        frame_digest = int().from_bytes(frame, "little", signed=False)

        self.__TCA9539.write_pins(frame_digest)

    def set_amp_rate(self, amp_ch1: str, amp_ch2: str, amp_ch3: str, update=True):
        """
        set amplification rate of each channel, amplification rates: "1", "2", "4", "8", "16", "32", "64", "128"
        :param update: update immediately
        :param amp_ch1: str
        :param amp_ch2: str
        :param amp_ch3: str
        :return:
        """
        self.ch1_amp = amp_ch1
        self.ch2_amp = amp_ch2
        self.ch3_amp = amp_ch3

        if update:
            self.update_changes()

    def set_LED(self, led1: bool = None, led2: bool = None, led3: bool = None, led4: bool = None, update=True):
        """
        turn LED indicator on/off (True/False)
        :param update: update immediately
        :param led1: bool
        :param led2: bool
        :param led3: bool
        :param led4: bool
        :return:
        """
        if led1 is None:
            led1 = self.leds[0]

        if led2 is None:
            led2 = self.leds[1]

        if led3 is None:
            led3 = self.leds[2]

        if led4 is None:
            led4 = self.leds[3]

        self.leds[0] = led1
        self.leds[1] = led2
        self.leds[2] = led3
        self.leds[3] = led4

        if update:
            self.update_changes()


class FPGACtl:

    def __init__(self, i2c_bus_path: str, addr: int = 0x30, debug: bool = False):
        """
        initialize a control interface for GTEM FPGA designed by Dr. Li
        :param i2c_bus_path: str, target i2c bus path, example: "/dev/i2c-2"
        :param addr: int, 7-bit chip address
        """
        self.interface_fd = wpi.wiringPiI2CSetupInterface(i2c_bus_path, addr)
        self.fpga_is_open = False
        self.chn_is_open = [False, False, False]
        # 0--500 1--1k 2--2k 3--4k 4--8k 5--10k 6--20k 7--32k
        # 8--40k 9--80k A--25k B--50k C--100k D--200k E--400k F--800k
        self.sample_rate_level = 0x0d
        # 0-16
        self.chn_amp_rate_level = [0, 0, 0]

        self.debug = debug

    def __send_command(self):
        """
        private command update method
        :return:
        """
        if self.fpga_is_open:
            fpga_status = 0xa0
        else:
            fpga_status = 0x50

        payload = [fpga_status | (self.chn_is_open[0] | self.chn_is_open[1] << 1 | self.chn_is_open[2] << 2),
                   (self.sample_rate_level % 16 << 4) | (self.chn_amp_rate_level[0] % 16),
                   (self.chn_amp_rate_level[1] % 16 << 4) | (self.chn_amp_rate_level[2] % 16)]

        reg = payload[0]
        payload = int().from_bytes(payload[1:], "little", signed=False)

        if self.debug:
            print("command:", bytes(payload).hex())
        wpi.wiringPiI2CWriteReg16(self.interface_fd, reg, payload)

    def start_FPGA(self):
        """
        start FPGA transmission
        :return:
        """
        self.fpga_is_open = True

        self.__send_command()

    def stop_FPGA(self):
        """
        stop FPGA transmission
        :return:
        """
        self.fpga_is_open = False

        self.__send_command()

    def enable_channels(self, ch1: bool = True, ch2: bool = True, ch3: bool = True):
        """
        set each channel's status (True: start / False: stop)
        :param ch1: bool
        :param ch2: bool
        :param ch3: bool
        :return:
        """
        self.chn_is_open[0] = ch1
        self.chn_is_open[1] = ch2
        self.chn_is_open[2] = ch3

        # if self.debug:
        #     self.__send_command()

    def set_sample_rate_level(self, sample_rate_level):
        """
        set sample rate level,
        0--500  1--1k   2--2k   3--4k   4--8k   5--10k  6--20k  7--32k
        8--40k  9--80k  A--25k  B--50k  C--100k D--200k E--400k F--800k
        :param sample_rate_level: int
        :return:
        """
        self.sample_rate_level = sample_rate_level

        # if self.debug:
        #     self.__send_command()

    def set_amp_rate_of_channels(self, ch1_amp, ch2_amp, ch3_amp):
        """
        set the amplification rate of each channel, level from 0x00 to 0x0f
        :param ch1_amp: int
        :param ch2_amp: int
        :param ch3_amp: int
        :return:
        """
        self.chn_amp_rate_level[0] = ch1_amp
        self.chn_amp_rate_level[1] = ch2_amp
        self.chn_amp_rate_level[2] = ch3_amp

        # if self.debug:
        #     self.__send_command()


if __name__ == '__main__':
    import os
    import time

    os.system("sudo chown -Rh pi /dev")

    chip1 = TCA9554("/dev/i2c-2", 0x20)
    chip2 = TCA9554("/dev/i2c-2", 0x21)
    chip3 = TCA9554("/dev/i2c-2", 0x23)
    chip4 = TCA9539("/dev/i2c-2", 0x74)
    fpga = FPGACtl("/dev/i2c-2", debug=True)

    chip1.set_pin_mode(0x00)
    chip2.set_pin_mode(0x00)
    chip3.set_pin_mode(0x00)
    chip4.set_pin_mode(0x0000)

    chip1.write_pins(0x01)
    chip2.write_pins(0x02)
    chip3.write_pins(0x03)
    chip4.write_pins(0x1234)

    print("chip1 TCA9554 for CH1 verification result: {}".format(chip1.read_output_pins() == 0x01))
    print("chip2 TCA9554 for CH2 verification result: {}".format(chip2.read_output_pins() == 0x02))
    print("chip3 TCA9554 for CH3 verification result: {}".format(chip3.read_output_pins() == 0x03))
    print("chip4 TCA9539 verification result: {}".format(chip4.read_output_pins() == 0x1234))

    time.sleep(0.5)

    chip1.write_pins(0xff)
    chip2.write_pins(0xff)
    chip3.write_pins(0xff)
    chip4.write_pins(0xffff)

    fpga.enable_channels(True, True, True)
    fpga.set_sample_rate_level(0x00)
    fpga.set_amp_rate_of_channels(0x0f, 0x0f, 0x0f)
    time.sleep(0.001)

    fpga.start_FPGA()

    time.sleep(1)
    fpga.stop_FPGA()
