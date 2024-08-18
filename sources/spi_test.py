#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: System_Installation.md
# Filename: spi_test
# Created on: 2023/9/22
import struct

from modules.spi import FPGACom, FPGACtl
from modules.i2c import AmpRateCtl, BandWidthCtl
import time

TEST_FILENAME = "test.bin"

LIVE = True

if __name__ == '__main__':
    print("initializing FPGA controller")
    ctl = FPGACtl("/dev/i2c-2", debug=True)

    print("initializing FPGA communication interface")
    com = FPGACom(to_file_only=True, ctl=ctl, debug=True, multiprocessing=True)

    print("starting communication interface")
    com.start()

    print("setting output file: {}".format(TEST_FILENAME))
    com.set_output_file(TEST_FILENAME)

    convert_sheet = ["500", "1K", "2K", "4K", "8K", "10K", "20K", "32K",
                     "40K", "80K", "25K", "50K", "100K", "200K", "400K", "800K"]

    sample_rate = 0x0d
    print("setting sample rate: {}".format(convert_sheet[sample_rate]))
    ctl.set_sample_rate_level(sample_rate)
    com.set_batch_size(sample_rate)

    print("setting amp rate: x1")
    ctl.set_amp_rate_of_channels("1", "1", "1")

    print("current FPGA status: {}".format(ctl.read_status().model_dump_json(indent=2)))
    # input("(press ENTER to start recording)")

    ctl.enable_channels(True, True, True)
    print("before start FPGA status: {}".format(ctl.read_status().model_dump_json(indent=2)))

    input("press enter to start")

    com.open()
    print("after start FPGA status: {}".format(ctl.read_status().model_dump_json(indent=2)))

    input("(press ENTER to stop recording)")
    # time.sleep(3)

    com.close()
    com.kill()
    ctl.reset()

    print("file saved in \"{}\"".format(TEST_FILENAME))

    f = open(TEST_FILENAME, "rb")

    print("first 20 frames of data:")
    print("   CH1      CH2      CH3")
    for i in range(20):
        print("  ", f.read(4).hex(), f.read(4).hex(), f.read(4).hex())

    f.seek(0)
    print("verifying data collected")
    n = 0
    err_frame_n = 0
    err_log = []
    headers = [0x05, 0x06, 0x07]
    EXIT = False
    while not EXIT:
        no_err = True
        for ch_n in range(3):
            chunk = f.read(4)[1:]
            if len(chunk) < 3:
                EXIT = True
                break

            num = int().from_bytes(chunk, byteorder='big', signed=False)

            # if chunk[0] != headers[ch_n]:
            #     err_log.append("invalid header 0x{} (should be 0x{}) at ch{} in frame NO.{} ({} clocks) detected".format(
            #         bytes((chunk[0],)).hex(), bytes((headers[ch_n],)).hex(), ch_n + 1, n + 1, (n + 1) * 3 * 32
            #     ))

            if num != n + 1:
                err_log.append(
                    "invalid channel data 0x{} (should be 0x{}) at ch{} in frame NO.{} ({} clocks) detected".format(
                        chunk.hex(), (n + 1).to_bytes(3, byteorder='big', signed=False).hex(),
                        ch_n + 1, n + 1, (n + 1) * 3 * 32
                    ))
                no_err = False

            # if num != 0x5aa55a:
            #     err_log.append(
            #         "invalid channel data 0x{} (should be 0x{}) at ch{} in frame NO.{} ({} clocks) detected".format(
            #             chunk[1:].hex(), (0x5aa55a).to_bytes(3, byteorder='big', signed=False).hex(),
            #             ch_n + 1, n + 1, (n + 1) * 3 * 32
            #         ))
            #     no_err = False

        if not no_err:
            err_frame_n += 1

        n += 1

    f.close()

    print(
        "{} errs detected in total {} frames, {} err frames, rate of error: {}, detailed information shown below: ".format(
            len(err_log), n, err_frame_n, 100 * err_frame_n / n))

    if len(err_log) < 20:
        for i, ele in enumerate(err_log):
            print(" {:0>2d}. {}".format(i + 1, ele))
    else:
        for i, ele in enumerate(err_log[:20]):
            print(" {:0>2d}. {}".format(i + 1, ele))
        print(" ...and {} more".format(len(err_log) - 9))
