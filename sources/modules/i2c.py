#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: i2c
# Created on: 2022/12/2

import wiringpi as wpi

class TCA9554:

    def __init__(self, i2c_bus_path: str, addr: int = 0x21):
        """
        initialize a control interface for TCA9554 I/O extension chip
        :param i2c_bus: str, target i2c bus path, example: "/dev/i2c-2"
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
        wpi.wiringPiI2CWriteReg8(self.interface_fd, 0x03, mode)

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


if __name__ == '__main__':
    chip1 = TCA9554("/dev/i2c-2", 0x20)
    chip2 = TCA9554("/dev/i2c-2", 0x21)
    chip3 = TCA9554("/dev/i2c-2", 0x23)

    chip1.set_pin_mode(0x00)
    chip2.set_pin_mode(0x00)
    chip3.set_pin_mode(0x00)

    chip1.write_pins(0x01)
    chip2.write_pins(0x02)
    chip3.write_pins(0x03)

    print("chip1 verification result: {}".format(chip1.read_output_pins() == 0x01))
    print("chip2 verification result: {}".format(chip2.read_output_pins() == 0x02))
    print("chip3 verification result: {}".format(chip3.read_output_pins() == 0x03))
