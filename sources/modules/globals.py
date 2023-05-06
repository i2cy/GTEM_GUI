#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: globals
# Created on: 2023/3/21

REAL_TIME_PLOT_XRANGES = (-5, 0)
REAL_TIME_PLOT_YRANGES = (-1.2 * 10 ** 7, 1.2 * 10 ** 7)
REAL_TIME_PLOT_XTITLE = "time(s)"
SF_PLOT_XTITLE = "time(ms)"
REAL_TIME_MAX_VIEW_TIME = 0.2

MAX_BUFFER_TIME = 600

REAL_TIME_LINE_COLOR = (255, 168, 56)
REAL_TIME_ALL_COLORS = ((255, 168, 56),
                        (18, 145, 255),
                        (60, 255, 20))
REAL_TIME_LINE_WIDTH = 1.7

SEC_FILED_XRANGE = (-1.4, 1)
SEC_FILED_YRANGE = (0, 7)

I2C_BUS = "/dev/i2c-2"
SD_PATH = "/dev/mmcblk1p1"
MOUNT_PATH = "/mnt"

CLIP_TIME_SEC = 3600
