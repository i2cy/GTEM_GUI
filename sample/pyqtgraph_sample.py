#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: pyqtgraph_sample
# Created on: 2022/9/11

import pyqtgraph as pg
import numpy as np
import time
from pyqtgraph.Qt import QtCore

app = pg.QtGui.QApplication([])
win = pg.GraphicsWindow(title="动态更新数据")
win.resize(600, 300)
p = win.addPlot()
data = list(np.zeros(5 * 50))
t0 = time.time()
x = list(np.linspace(-5, 0, 5 * 50))
curve = p.plot(data)
ptr = 0
p.setRange(xRange=[-5, 0])  # 将横坐标的范围限定为[-100,0]
p.setLimits(yMin=0, yMax=1)  # 横坐标的最大值为0


def update1():
    global data, ptr
    data[:-1] = data[1:]  # shift data in the array one sample left

    data[-1] = np.random.normal()

    ptr += 1
    curve.setData(data)
    curve.setPos(ptr, 0)


def update():
    global data, curve, ptr
    x_range = p.getViewBox().viewRange()[0]
    x_range = [x_range[0] + 0.02, x_range[1] + 0.02]
    x.pop(0)
    x.append(time.time() - t0)
    #print(x_range)
    #p.setLimits(xMax=x[-1])
    #p.setLimits(xMin=x[0])
    #p.setRange(xRange=x_range, padding=0)
    data.pop(0)
    data.append(np.random.random())

    curve.setData(x, data)
    ptr -= 0.02
    curve.setPos(-x[0], 0)  # 给图形对象设置新的坐标值
    # 参数1：x轴起点坐标
    # 参数2：y轴起点坐标


timer = QtCore.QTimer()
timer.timeout.connect(update1)
timer.start(20)
app.exec_()
