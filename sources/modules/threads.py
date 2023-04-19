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
from .uart import GPS, GPS_DEVICE, GPS_BR
from .spi_dev import DATA_BATCH, DATA_FRAME_SIZE
from queue import Empty
from multiprocessing import Manager, Process, Queue


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


class GPSUpdaterThread(QThread):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.gps = GPS(GPS_DEVICE, GPS_BR)
        self.gps_status = False

    def run(self) -> None:
        status = self.gps.manually_update()
        if status:
            if self.gps.loc_status:
                self.parent.label_gpsStatus_2.setText("成功定位")
                self.gps_status = True
            else:
                self.parent.label_gpsStatus_2.setText("正在搜星")
                self.gps_status = False
        else:
            self.parent.label_gpsStatus_2.setText("不可用")
            self.gps_false = False


class DataUpdaterThread(QThread):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.timestamp = 0.0
        self.dt_i = 1 / int(self.parent.comboBox_sampleRate.currentText())
        self.fifo_ch1: Queue = self.parent.fpga_com.mp_ch1_data_queue_x400
        self.fifo_ch2: Queue = self.parent.fpga_com.mp_ch2_data_queue_x400
        self.fifo_ch3: Queue = self.parent.fpga_com.mp_ch3_data_queue_x400

    def reset(self):
        self.dt_i = 1 / int(self.parent.comboBox_sampleRate.currentText())
        self.timestamp = 0.0

    def run(self):
        self.parent.amp_ctl.set_LED(led3=not self.parent.amp_ctl.leds[2])

        try:
            data = self.fifo_ch1.get_nowait()
            if len(data):
                self.parent.buf_realTime_ch1.updateBatch(
                    data,
                    np.linspace(
                        self.timestamp,
                        self.timestamp + len(data) * self.dt_i, len(data),
                        dtype=np.float32
                    )
                )
        except Empty:
            pass
        try:
            data = self.fifo_ch2.get_nowait()
            if len(data):
                self.parent.buf_realTime_ch2.updateBatch(
                    data,
                    np.linspace(
                        self.timestamp,
                        self.timestamp + len(data) * self.dt_i, len(data),
                        dtype=np.float32
                    )
                )
        except Empty:
            pass
        try:
            data = self.fifo_ch3.get_nowait()
            if len(data):
                self.parent.buf_realTime_ch3.updateBatch(
                    data,
                    np.linspace(
                        self.timestamp,
                        self.timestamp + len(data) * self.dt_i, len(data),
                        dtype=np.float32
                    )
                )
        except Empty:
            pass

        try:
            self.timestamp += len(data) * self.dt_i
        except:
            pass


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
        self.parent.amp_ctl.set_LED(led2=True)

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

        self.parent.amp_ctl.set_LED(led2=False)

    def run(self):
        # if tab stays in page of real time graph
        sample_rate = int(self.parent.comboBox_sampleRate.currentText())
        emit_rate = int(self.parent.comboBox_radiateFreq.currentText())
        tab_index = self.parent.tabWidget_channelGraph.currentIndex()
        current_buf = None

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

        y_range = list(REAL_TIME_PLOT_YRANGES)
        if y_range[0] > data[0].min():
            y_range[0] = data[0].min() * 0.05

        if y_range[1] < data[1].max():
            y_range[1] = data[1].max() * 0.05

        xmin = data[0][0]
        xmax = data[0][-1]
        self.last_rander_limits = (xmin, xmax)
        self.last_rander_range = (x_range, y_range)
