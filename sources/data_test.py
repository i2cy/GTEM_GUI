#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: System_Installation.md
# Filename: data_test
# Created on: 2024/12/30


from modules.data import PlotBuf
import numpy as np


p = PlotBuf(buf_length=150, sample_rate=50, freq=1)
p.updateBatch(range(0,100), range(100,200))

print(p.getBuf(3))
p.updateBatch(range(0,100), range(100,200))

print(p.getBuf(3))
p.updateBatch(range(100,200), range(200,300))

print(p.getBuf(3))
print(p.getBuf(3))
print(p.getBuf(3))

