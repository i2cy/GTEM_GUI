#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: System_Installation.md
# Filename: spi_test
# Created on: 2023/9/22

from modules.spi import FPGACom, FPGAStat, FPGACtl


TEST_FILENAME = "test.bin"


if __name__ == '__main__':

    print("initializing FPGA communication interface")
    com = FPGACom(to_file_only=True, debug=True)

    print("initializing FPGA controller")
    ctl = FPGACtl("/dev/i2c-2")

    print("starting communication interface")
    com.start()

    print("setting output file: {}".format(TEST_FILENAME))
    com.set_output_file(TEST_FILENAME)

    print("setting sample rate: 200K")
    ctl.set_sample_rate_level(0xd)
    com.set_batch_size(0xd)

    print("setting amp rate: x1")
    ctl.set_amp_rate_of_channels("1", "1", "1")

    print("current FPGA status: {}".format(com.get_status().model_dump_json(indent=2)))
    input("(press ENTER to start recording)")

    ctl.enable_channels(True, True, True)
    print("current FPGA status: {}".format(com.get_status().model_dump_json(indent=2)))

    com.open()
    ctl.start_FPGA()

    input("(press ENTER to stop recording)")

    ctl.stop_FPGA()
    com.close()

    print("file saved in \"{}\"".format(TEST_FILENAME))

    f = open(TEST_FILENAME, "rb")

    print("first 2 frame of data:")
    print("        CH1        CH2         CH3")
    for i in range(2):
        print("  ", f.read(3).hex(), f.read(3).hex(), f.read(3).hex())
