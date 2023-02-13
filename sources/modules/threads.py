#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: threads
# Created on: 2022/9/10

import numpy as np
from PyQt5.QtCore import QThread
from PyQt5.Qt import pyqtSignal
import time


class TestThread(QThread):

    def __init__(self):
        super(TestThread, self).__init__()

    def run(self):
        for i in range(100):
            print(i)
            time.sleep(0.5)


class MainGraphUpdaterThread(QThread):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def
