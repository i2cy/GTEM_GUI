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
from .globals import *
from .gtem import Gtem24
from multiprocessing import Manager, Process


class TestThread(QThread):

    def __init__(self):
        super(TestThread, self).__init__()

    def run(self):
        for i in range(100):
            print(i)
            time.sleep(0.5)


class SecGraphUpdaterThread(QThread):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.last_rander_tab = 0
        self.last_rander_data1 = ()
        self.last_rander_data2 = ()
        self.last_rander_data3 = ()

    def update_graph(self):
        if self.last_rander_tab == 1:  # channel 1
            current_data = self.parent.sfPlot_ch1
            current_data.setData(*self.last_rander_data1)

        elif self.last_rander_tab == 2:  # channel 2
            current_data = self.parent.sfPlot_ch2
            current_data.setData(*self.last_rander_data1)

        elif self.last_rander_tab == 3:  # channel 3
            current_data = self.parent.sfPlot_ch3
            current_data.setData(*self.last_rander_data1)

        else:  # channel all
            x, sig = self.last_rander_data1
            self.parent.sfPlot_all_ch1.setData(x, sig)
            x, sig = self.last_rander_data2
            self.parent.sfPlot_all_ch2.setData(x, sig)
            x, sig = self.last_rander_data3
            self.parent.sfPlot_all_ch3.setData(x, sig)

    def run(self):
        # if tab stays in page of sec field graph
        add_time = int(self.parent.comboBox_secFieldStackingTime.currentText())
        sample_rate = int(self.parent.comboBox_sampleRate.currentText())
        emit_rate = int(self.parent.comboBox_radiateFreq.currentText())
        tab_index = self.parent.tabWidget_channelGraph.currentIndex()
        current_buf = None
        current_data = None

        self.last_rander_tab = tab_index

        if tab_index == 1:  # channel 1
            current_buf = self.parent.buf_realTime_ch1
            data = current_buf.getBuf(sample_rate * add_time)
            self.last_rander_data1 = Gtem24(sample_rate=sample_rate,
                                            emit_freq=emit_rate,
                                            data=data[1][1]).gateTraceSecFieldExtract(add_time)

        elif tab_index == 2:  # channel 2
            current_buf = self.parent.buf_realTime_ch2
            data = current_buf.getBuf(sample_rate * add_time)
            self.last_rander_data1 = Gtem24(sample_rate=sample_rate,
                                            emit_freq=emit_rate,
                                            data=data[1][1]).gateTraceSecFieldExtract(add_time)

        elif tab_index == 3:  # channel 3
            current_buf = self.parent.buf_realTime_ch3
            data = current_buf.getBuf(sample_rate * add_time)
            self.last_rander_data1 = Gtem24(sample_rate=sample_rate,
                                            emit_freq=emit_rate,
                                            data=data[1][1]).gateTraceSecFieldExtract(add_time)

        else:  # channel all
            # ch1 process spawn
            data = self.parent.buf_realTime_ch1.getBuf(sample_rate * add_time)
            c_ch1 = Gtem24(sample_rate=sample_rate,
                           emit_freq=emit_rate,
                           data=data[1][1])
            p_ch1 = c_ch1.gateTraceSecFieldExtract(add_time, no_wait=True)

            # ch2 process spawn
            data = self.parent.buf_realTime_ch2.getBuf(sample_rate * add_time)
            c_ch2 = Gtem24(sample_rate=sample_rate,
                           emit_freq=emit_rate,
                           data=data[1][1])
            p_ch2 = c_ch2.gateTraceSecFieldExtract(add_time, no_wait=True)

            # ch3 process spawn
            data = self.parent.buf_realTime_ch3.getBuf(sample_rate * add_time)
            c_ch3 = Gtem24(sample_rate=sample_rate,
                           emit_freq=emit_rate,
                           data=data[1][1])
            p_ch3 = c_ch3.gateTraceSecFieldExtract(add_time, no_wait=True)

            # wait for results
            self.last_rander_data1 = c_ch1.wait(p_ch1)
            self.last_rander_data2 = c_ch2.wait(p_ch2)
            self.last_rander_data3 = c_ch3.wait(p_ch3)


class MainGraphUpdaterThread(QThread):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.last_rander_tab = 0
        self.last_rander_data1 = ()
        self.last_rander_data2 = ()
        self.last_rander_data3 = ()
        self.last_rander_limits = ()
        self.last_rander_range = ()

    def update_graph(self):
        if self.last_rander_tab == 1:  # channel 1
            self.parent.rtPlot_ch1.setData(*self.last_rander_data1)

        elif self.last_rander_tab == 2:  # channel 2
            self.parent.rtPlot_ch2.setData(*self.last_rander_data1)

        elif self.last_rander_tab == 3:  # channel 3
            self.parent.rtPlot_ch3.setData(*self.last_rander_data1)

        else:  # channel all
            self.parent.rtPlot_allch1.setData(*self.last_rander_data1)
            self.parent.rtPlot_allch2.setData(*self.last_rander_data2)
            self.parent.rtPlot_allch3.setData(*self.last_rander_data3)

        self.parent.rtPlotWeight_all.setLimits(xMin=self.last_rander_limits[0], xMax=self.last_rander_limits[1])
        self.parent.rtPlotWeight_all.setRange(xRange=self.last_rander_range[0], yRange=self.last_rander_range[1],
                                              padding=0)
        self.parent.rtPlotWeight_ch1.setLimits(xMin=self.last_rander_limits[0], xMax=self.last_rander_limits[1])
        self.parent.rtPlotWeight_ch1.setRange(xRange=self.last_rander_range[0], yRange=self.last_rander_range[1],
                                              padding=0)
        self.parent.rtPlotWeight_ch2.setLimits(xMin=self.last_rander_limits[0], xMax=self.last_rander_limits[1])
        self.parent.rtPlotWeight_ch2.setRange(xRange=self.last_rander_range[0], yRange=self.last_rander_range[1],
                                              padding=0)
        self.parent.rtPlotWeight_ch3.setLimits(xMin=self.last_rander_limits[0], xMax=self.last_rander_limits[1])
        self.parent.rtPlotWeight_ch3.setRange(xRange=self.last_rander_range[0], yRange=self.last_rander_range[1],
                                              padding=0)

    def run(self):
        # if tab stays in page of real time graph
        sample_rate = int(self.parent.comboBox_sampleRate.currentText())
        emit_rate = int(self.parent.comboBox_radiateFreq.currentText())
        tab_index = self.parent.tabWidget_channelGraph.currentIndex()
        current_buf = None

        self.last_rander_tab = tab_index

        if tab_index == 1:  # ch1 args
            current_buf = self.parent.buf_realTime_ch1
            current_plot = self.parent.rtPlotWeight_ch1
        elif tab_index == 2:  # ch2 args
            current_buf = self.parent.buf_realTime_ch2
            current_plot = self.parent.rtPlotWeight_ch2
        elif tab_index == 3:  # ch3 args
            current_buf = self.parent.buf_realTime_ch3
            current_plot = self.parent.rtPlotWeight_ch3
        else:  # overview args
            current_plot = self.parent.rtPlotWeight_all

        max_view_range = 4 / emit_rate
        view_range = int(max_view_range * sample_rate)

        if tab_index:  # when not in overview tab
            dt, data = current_buf.getBuf(view_range)
            x_range = current_plot.getViewBox().viewRange()
            y_range = x_range[1]
            x_range = x_range[0]
            x_start = (x_range[0] + dt) * max_view_range // max_view_range
            x_range = [x_start, x_start + max_view_range]

            self.last_rander_data1 = data

        else:  # when in overview tab
            dt, data = self.parent.buf_realTime_ch1.getBuf(view_range)
            self.last_rander_data1 = data
            dt, data = self.parent.buf_realTime_ch2.getBuf(view_range)
            self.last_rander_data2 = data
            dt, data = self.parent.buf_realTime_ch3.getBuf(view_range)
            self.last_rander_data3 = data
            x_range = current_plot.getViewBox().viewRange()
            y_range = x_range[1]
            x_range = x_range[0]
            x_range = [x_range[0] + dt, x_range[1] + dt]

        xmin = data[0][0]
        xmax = data[0][-1]
        self.last_rander_limits = (xmin, xmax)
        self.last_rander_range = (x_range, y_range)
