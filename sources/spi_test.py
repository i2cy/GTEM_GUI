#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: System_Installation.md
# Filename: spi_test
# Created on: 2023/9/22
import struct

from modules.spi import FPGACom, FPGACtl
import time

TEST_FILENAME = "test.bin"

LIVE = True

if __name__ == '__main__':
    print("initializing FPGA controller")
    ctl = FPGACtl("/dev/i2c-2", debug=True)

    print("initializing FPGA communication interface")
    com = FPGACom(to_file_only=True, ctl=ctl, debug=True)

    print("starting communication interface")
    com.start()

    print("setting output file: {}".format(TEST_FILENAME))
    com.set_output_file(TEST_FILENAME)

    print("setting sample rate: 50K")
    ctl.set_sample_rate_level(0xa)
    com.set_batch_size(0xa)

    print("setting amp rate: x1")
    ctl.set_amp_rate_of_channels("0", "0", "0")

    print("current FPGA status: {}".format(ctl.read_status().model_dump_json(indent=2)))
    # input("(press ENTER to start recording)")

    ctl.enable_channels(True, True, True)
    print("before start FPGA status: {}".format(ctl.read_status().model_dump_json(indent=2)))

    com.open()
    print("after start FPGA status: {}".format(ctl.read_status().model_dump_json(indent=2)))

    input("(press ENTER to stop recording)")
    # time.sleep(3)

    com.close()
    com.kill()
    ctl.reset()

    print("file saved in \"{}\"".format(TEST_FILENAME))

    f = open(TEST_FILENAME, "rb")

    print("first 2 frame of data:")
    print("   CH1      CH2      CH3")
    for i in range(6):
        print("  ", f.read(4).hex(), f.read(4).hex(), f.read(4).hex())

    f.seek(0)
    print("verifying data collected (1 byte of header info ignored in each channel)")
    n = 0
    err_log = []
    headers = [0x05, 0x06, 0x07]
    EXIT = False
    while not EXIT:
        for ch_n in range(3):
            chunk = f.read(4)
            if len(chunk) < 4:
                EXIT = True
                break

            num = int().from_bytes(chunk[1:], byteorder='big', signed=False)

            if chunk[0] != headers[ch_n]:
                err_log.append("invalid header 0x{} (should be 0x{}) at ch{} in frame NO.{} ({} clocks) detected".format(
                    bytes((chunk[0],)).hex(), bytes((headers[ch_n],)).hex(), ch_n + 1, n + 1, (n + 1) * 3 * 32
                ))

            if num != n + 1:
                err_log.append("invalid channel data 0x{} (should be 0x{}) at ch{} in frame NO.{} ({} clocks) detected".format(
                    chunk[1:].hex(), (n + 1).to_bytes(3, byteorder='big', signed=False).hex(),
                    ch_n + 1, n + 1, (n + 1) * 3 * 32
                ))

        n += 1

    f.close()

    print("{} err detected, detailed information shown below: ".format(len(err_log)))

    if len(err_log) < 9:
        for i, ele in enumerate(err_log):
            print(" {}. {}".format(i + 1, ele))
    else:
        for i, ele in enumerate(err_log[:9]):
            print(" {}. {}".format(i + 1, ele))
        print(" ...and {} more".format(len(err_log) - 9))

    del com
