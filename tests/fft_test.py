#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: System_Installation.md
# Filename: fft_test
# Created on: 2024/7/28


import matplotlib.pyplot as plt
import numpy as np
from scipy.fftpack import fft
from tqdm import tqdm


def main():
    # init
    filename = input("target filename: ")
    if filename == "":
        filename = "/home/pi/test.bin"

    sample_rate = input("set sample rate for calculation: ")
    sample_rate = int(sample_rate)

    # read data
    f = open(filename, "rb")
    frame_num = 0
    while True:
        data = f.read(12)  # 4B per channel
        if len(data) != 12:
            break
        else:
            frame_num += 1
    total_seconds = frame_num // sample_rate

    print("{} frames found, {} valid second of data".format(frame_num, total_seconds))

    # crop first 1000 frames
    pre_frames_ch1 = []
    pre_frames_ch2 = []
    pre_frames_ch3 = []

    f.seek(0)

    for i in range(1000):
        pre_frames_ch1.append(int().from_bytes(f.read(4)[1:], "big", signed=True))
        pre_frames_ch2.append(int().from_bytes(f.read(4)[1:], "big", signed=True))
        pre_frames_ch3.append(int().from_bytes(f.read(4)[1:], "big", signed=True))

    print(pre_frames_ch1[:50])

    x = np.linspace(0, 1000 / sample_rate, 1000)
    plt.plot(x, pre_frames_ch1, label="ch1", alpha=0.4)

    plt.plot(x, pre_frames_ch2, label="ch2", alpha=0.4)

    plt.plot(x, pre_frames_ch3, label="ch3", alpha=0.4)
    plt.title("first 1000 frames of all 3 CH (SR: {}Hz)".format(sample_rate))
    plt.xlabel("time(s)")

    plt.legend()
    plt.show()

    # calculate fft
    f.seek(0)
    ch1_x = []
    ch2_x = []
    ch3_x = []
    fft_ch1_y = np.zeros(sample_rate // 2, dtype=np.float32)
    fft_ch2_y = np.zeros(sample_rate // 2, dtype=np.float32)
    fft_ch3_y = np.zeros(sample_rate // 2, dtype=np.float32)
    for i in tqdm(range(total_seconds), desc="Calculating FFT"):
        # prepare data
        for ele in range(sample_rate):
            ch1_x.append(int().from_bytes(f.read(4)[1:], "big", signed=True))
            ch2_x.append(int().from_bytes(f.read(4)[1:], "big", signed=True))
            ch3_x.append(int().from_bytes(f.read(4)[1:], "big", signed=True))

        # fft
        k_dim = sample_rate * total_seconds
        fft_ch1_y += np.abs(fft(ch1_x))[:sample_rate // 2] / k_dim
        fft_ch2_y += np.abs(fft(ch2_x))[:sample_rate // 2] / k_dim
        fft_ch3_y += np.abs(fft(ch3_x))[:sample_rate // 2] / k_dim

        # clear cache
        ch1_x.clear()
        ch2_x.clear()
        ch3_x.clear()

    print("fft complete, displaying plots")

    x = np.linspace(0, sample_rate // 2, sample_rate // 2)
    plt.plot(x, fft_ch1_y)
    plt.title("FFT result of CH1 (SR: {}Hz)".format(sample_rate))
    plt.xlabel("Freq (Hz)")

    plt.show()

    plt.plot(x, fft_ch2_y)
    plt.title("FFT result of CH2 (SR: {}Hz)".format(sample_rate))
    plt.xlabel("Freq (Hz)")

    plt.show()

    plt.plot(x, fft_ch3_y)
    plt.title("FFT result of CH3 (SR: {}Hz)".format(sample_rate))
    plt.xlabel("Freq (Hz)")

    plt.show()


if __name__ == '__main__':
    main()
