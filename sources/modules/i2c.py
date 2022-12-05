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


class FPGACtl:

    def __init__(self, i2c_bus_path: str, addr: int = 0x30):
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

    def start_FPGA(self):
        """
        start FPGA transmission
        :return:
        """
        payload = [0xa0 | (self.chn_is_open[0] | self.chn_is_open[1] << 1 | self.chn_is_open[2] << 2),
                   (self.sample_rate_level % 16 << 4) | (self.chn_amp_rate_level[0] % 16),
                   (self.chn_amp_rate_level[1] % 16 << 4) | (self.chn_amp_rate_level[2] % 16)]
        self.fpga_is_open = True

        cmd = bytes(payload)
        self.interface_fd = wpi.wiringPiI2CWrite(self.interface_fd, cmd)

    def stop_FPGA(self):
        """
        stop FPGA transmission
        :return:
        """
        payload = [0x50 | (self.chn_is_open[0] | self.chn_is_open[1] << 1 | self.chn_is_open[2] << 2),
                   (self.sample_rate_level % 16 << 4) | (self.chn_amp_rate_level[0] % 16),
                   (self.chn_amp_rate_level[1] % 16 << 4) | (self.chn_amp_rate_level[2] % 16)]
        self.fpga_is_open = False

        cmd = bytes(payload)
        self.interface_fd = wpi.wiringPiI2CWrite(self.interface_fd, cmd)

    def enable_channels(self, ch1: bool = True, ch2: bool = True, ch3: bool = True):
        """

        :param ch1:
        :param ch2:
        :param ch3:
        :return:
        """





if __name__ == '__main__':
    chip1 = TCA9554("/dev/i2c-2", 0x20)
    chip2 = TCA9554("/dev/i2c-2", 0x21)
    chip3 = TCA9554("/dev/i2c-2", 0x23)
    chip4 = TCA9539("/dev/i2c-2", 0x74)

    chip1.set_pin_mode(0x00)
    chip2.set_pin_mode(0x00)
    chip3.set_pin_mode(0x00)
    chip4.set_pin_mode(0x0000)

    chip1.write_pins(0x01)
    chip2.write_pins(0x02)
    chip3.write_pins(0x03)
    chip4.write_pins(0x1234)

    print("chip1 verification result: {}".format(chip1.read_output_pins() == 0x01))
    print("chip2 verification result: {}".format(chip2.read_output_pins() == 0x02))
    print("chip3 verification result: {}".format(chip3.read_output_pins() == 0x03))
    print("chip4 verification result: {}".format(chip4.read_output_pins() == 0x1234))
