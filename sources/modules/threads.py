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
            # print(i)
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
        self.error_cnt = 0
        self.filename = None
        self.file_io = None

    def run(self) -> None:
        status = self.gps.manually_update()

        if status:
            if self.gps.loc_status:
                self.parent.label_gpsStatus_2.setText("成功定位")
                self.gps_status = True
                self.error_cnt = 0
            else:
                self.error_cnt += 1
                if self.error_cnt >= 15:
                    self.parent.label_gpsStatus_2.setText("正在搜星")
                    self.gps_status = False
        else:
            self.error_cnt += 1
            if self.error_cnt >= 15:
                self.parent.label_gpsStatus_2.setText("不可用")
                self.gps_false = False


class DataUpdaterThread(QThread):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.ts_zero = 0.0
        self.timestamp = 0.0
        self.dt_i = 1 / int(self.parent.comboBox_sampleRate.currentText())
        self.fifo_ch1: Queue = self.parent.fpga_com.mp_ch1_data_queue_x4
        self.fifo_ch2: Queue = self.parent.fpga_com.mp_ch2_data_queue_x4
        self.fifo_ch3: Queue = self.parent.fpga_com.mp_ch3_data_queue_x4

        self.last_batch_timestamp_start = 0.0

        self.ch1_dat = None
        self.ch2_dat = None
        self.ch3_dat = None

    def reset(self):
        self.dt_i = 1 / int(self.parent.comboBox_sampleRate.currentText())
        self.timestamp = 0.0
        self.ts_zero = 0.0

    def run(self):
        self.parent.amp_ctl.set_LED(led3=not self.parent.amp_ctl.leds[2])

        # file clip
        ts = time.time()
        tp = ts - self.parent.record_start_ts - self.ts_zero
        if tp > CLIP_TIME_SEC:
            filename = self.parent.staticGenerateFilename()
            abs_path = f"{MOUNT_PATH}/{filename}.bin"
            self.parent.fpga_com.set_output_file(abs_path)
            abs_path = f"{MOUNT_PATH}/{filename}_gps.txt"
            self.parent.gps_updater.gps.set_gps_file(abs_path)
            self.ts_zero = ts

        for i in range(6):

            if self.ch1_dat is None:
                try:
                    data = self.fifo_ch1.get_nowait()
                    if len(data):
                        # print(f"ch1 updated data with length {len(data)}")
                        self.ch1_dat = data

                except Empty:
                    pass

            if self.ch2_dat is None:
                try:
                    data = self.fifo_ch2.get_nowait()
                    if len(data):
                        # print(f"ch2 updated data with length {len(data)}")
                        self.ch2_dat = data

                except Empty:
                    pass

            if self.ch3_dat is None:
                try:
                    data = self.fifo_ch3.get_nowait()
                    if len(data):
                        # print(f"ch3 updated data with length {len(data)}")
                        self.ch3_dat = data

                except Empty:
                    pass

            try:
                if self.ch1_dat is not None and self.ch2_dat is not None and self.ch3_dat is not None:
                    self.timestamp = time.time() - self.parent.record_start_ts

                    x = np.linspace(
                        self.last_batch_timestamp_start,
                        self.timestamp, len(self.ch1_dat),
                        dtype=np.float32
                    )
                    self.parent.buf_realTime_ch1.updateBatch(self.ch1_dat, x)
                    self.parent.buf_realTime_ch2.updateBatch(self.ch2_dat, x)
                    self.parent.buf_realTime_ch3.updateBatch(self.ch3_dat, x)

                    self.ch1_dat = None
                    self.ch2_dat = None
                    self.ch3_dat = None

                    self.last_batch_timestamp_start = self.timestamp
                    # print("timestamp now:", self.last_batch_timestamp_start)
            except:
                pass

        # # print(f"fifo ch1 status: length = {self.fifo_ch1.qsize()}")


class MainGraphUpdaterThread(QThread):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.last_rander_tab = 0
        self.last_rander_data1 = ()
        self.last_rander_data2 = ()
        self.last_rander_data3 = ()
        self.last_render_limits = ()
        self.last_render_range = (REAL_TIME_PLOT_XRANGES, REAL_TIME_PLOT_YRANGES)

    def update_graph(self):
        self.parent.amp_ctl.set_LED(led2=True)

        tab_index = self.parent.tabWidget_channelGraph.currentIndex()

        if tab_index == 1:  # ch1 args
            current_plot = self.parent.rtPlotWeight_ch1
        elif tab_index == 2:  # ch2 args
            current_plot = self.parent.rtPlotWeight_ch2
        elif tab_index == 3:  # ch3 args
            current_plot = self.parent.rtPlotWeight_ch3
        else:  # overview args
            current_plot = self.parent.rtPlotWeight_all

        range_vb = current_plot.getViewBox().viewRange()
        y_range_vb = range_vb[1]
        x_range_vb = range_vb[0]

        y_range = list(self.last_render_range[1])
        d_min = min(self.last_rander_data1[1].min(),
                    self.last_rander_data2[1].min(),
                    self.last_rander_data3[1].min())
        d_max = max(self.last_rander_data1[1].max(),
                    self.last_rander_data2[1].max(),
                    self.last_rander_data3[1].max())
        t_hold = (y_range_vb[1] - y_range_vb[0]) * 0.1

        if abs(d_min) > abs(d_max):
            if d_min - y_range[0] > t_hold or d_min - y_range[0] < 0:
                d_min = abs(d_min * 1.03)
                y_range[0] = -d_min
                y_range[1] = d_min

        else:
            if y_range[1] - d_max > t_hold or y_range[1] - d_max < 0:
                d_max = abs(d_max * 1.03)
                y_range[0] = -d_max
                y_range[1] = d_max

        xmin = self.last_rander_data1[0][0]
        xmax = self.last_rander_data1[0][-1]

        x_range = (xmin, xmax)

        self.last_render_limits = x_range
        self.last_render_range = (x_range, y_range)
        # print(f"rt data length: ({len(self.last_rander_data1[0])}, {len(self.last_rander_data1[1])})")
        # print(f"rt render range: {self.last_render_range}")

        if tab_index == 1:  # channel 1
            self.parent.rtPlot_ch1.setData(*self.last_rander_data1)

        elif tab_index == 2:  # channel 2
            self.parent.rtPlot_ch2.setData(*self.last_rander_data2)

        elif tab_index == 3:  # channel 3
            self.parent.rtPlot_ch3.setData(*self.last_rander_data3)

        else:  # channel all
            self.parent.rtPlot_allch1.setData(*self.last_rander_data1)
            self.parent.rtPlot_allch2.setData(*self.last_rander_data2)
            self.parent.rtPlot_allch3.setData(*self.last_rander_data3)

        try:
            self.parent.rtPlotWeight_all.setLimits(xMin=self.last_render_limits[0], xMax=self.last_render_limits[1],
                                                   yMin=self.last_render_range[1][0], yMax=self.last_render_range[1][1])
            self.parent.rtPlotWeight_all.setRange(xRange=self.last_render_range[0], yRange=self.last_render_range[1],
                                                  padding=0)

            self.parent.rtPlotWeight_ch1.setLimits(xMin=self.last_render_limits[0], xMax=self.last_render_limits[1],
                                                   yMin=self.last_render_range[1][0], yMax=self.last_render_range[1][1])
            self.parent.rtPlotWeight_ch1.setRange(xRange=self.last_render_range[0], yRange=self.last_render_range[1],
                                                  padding=0)

            self.parent.rtPlotWeight_ch2.setLimits(xMin=self.last_render_limits[0], xMax=self.last_render_limits[1],
                                                   yMin=self.last_render_range[1][0], yMax=self.last_render_range[1][1])
            self.parent.rtPlotWeight_ch2.setRange(xRange=self.last_render_range[0], yRange=self.last_render_range[1],
                                                  padding=0)

            self.parent.rtPlotWeight_ch3.setLimits(xMin=self.last_render_limits[0], xMax=self.last_render_limits[1],
                                                   yMin=self.last_render_range[1][0], yMax=self.last_render_range[1][1])
            self.parent.rtPlotWeight_ch3.setRange(xRange=self.last_render_range[0], yRange=self.last_render_range[1],
                                                  padding=0)

        except Exception as err:
            print(f"range err, {self.last_render_range}")

        self.parent.amp_ctl.set_LED(led2=False)

    def run(self):
        self.parent.amp_ctl.set_LED(led4=True)
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

        dt, data = self.parent.buf_realTime_ch1.getBuf(view_range)
        self.last_rander_data1 = data
        dt, data = self.parent.buf_realTime_ch2.getBuf(view_range)
        self.last_rander_data2 = data
        dt, data = self.parent.buf_realTime_ch3.getBuf(view_range)
        self.last_rander_data3 = data

        self.parent.amp_ctl.set_LED(led4=False)
