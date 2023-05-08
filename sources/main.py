#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: sources
# Filename: main
# Created on: 2022/9/3


import sys
import os
import queue
import threading
import time
import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, \
    QSizePolicy, QListWidgetItem, QMessageBox
from PyQt5.QtGui import QIcon, QImage, QPixmap, QKeyEvent, QMouseEvent, QPainterPath
from PyQt5.QtCore import Qt, QTimer
from i2cylib.utils import DirTree

from mainWindow import Ui_MainWindow
from modules.data import PlotBuf
from modules.gtem import Gtem24File, Gtem24
from modules.graphic import init_graph
from modules.globals import *
from modules.threads import MainGraphUpdaterThread, SecGraphUpdaterThread, GPSUpdaterThread, DataUpdaterThread
# from modules.spi_dev import FPGACtl, FPGACom
# from modules.i2c import BandWidthCtl, AmpRateCtl

TEST = False
DECOY = False


class UIReceiver(QMainWindow, Ui_MainWindow, QApplication):

    def __init__(self):

        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # flags
        self.flag_recording = False

        # menu
        self.toolButton_GTEM.clicked.connect(self.onButtonGTEMClicked)
        # self.toolButton_historyFile.clicked.connect(self.onButtonHistoryClicked)

        # bottom bar components
        self.toolButton_startRecording.setEnabled(False)
        self.toolButton_startRecording.clicked.connect(self.onButtonStartRecordClicked)
        self.toolButton_settings.clicked.connect(self.onButtonSettingClicked)
        self.toolButton_mainMenu.clicked.connect(self.onButtonReturnToMenuClicked)

        self.toolButton_settings.setVisible(False)
        self.label_filenameHeader_2.setVisible(False)
        self.label_titleFilenameHeader.setVisible(False)

        # top bar
        self.pushButton_graphSwitchToRealTime.clicked.connect(self.onButtonSwitchToRealTimeClicked)
        self.pushButton_graphSwitchToSecField.clicked.connect(self.onButtonSwitchToSecFieldClicked)

        # history top bar
        # self.pushButton_graphSwitchToRealTime_hist.clicked.connect(self.onButtonSwitchToRealTimeClicked)
        # self.pushButton_graphSwitchToSecField_hist.clicked.connect(self.onButtonSwitchToSecFieldClicked)

        # history bottom bar
        # self.toolButton_historyMainMenu.clicked.connect(self.onButtonReturnToMenuClicked)
        # self.toolButton_histSelectFile.clicked.connect(self.actionSelectHistoryFile)
        # self.horizontalSlider_historyView.sliderMoved.connect(self.doUpdateHistoryRtGraph)

        self.history_file = Gtem24File("")

        pg.setConfigOption("background", "k")
        pg.setConfigOption('foreground', 'w')

        # sec field graph init
        self.sfPlotWeight_all = init_graph(self, self.gridLayout_allGraph,
                                           xtitle=SF_PLOT_XTITLE,
                                           xrange=SEC_FILED_XRANGE,
                                           yrange=SEC_FILED_YRANGE,
                                           disable_mouse=True,
                                           enable_legend=True,
                                           log_mode=True)

        self.sfPlotWeight_ch1 = init_graph(self, self.gridLayout_ch1Graph,
                                           xtitle=SF_PLOT_XTITLE,
                                           xrange=SEC_FILED_XRANGE,
                                           yrange=SEC_FILED_YRANGE,
                                           disable_mouse=True,
                                           enable_legend=True,
                                           log_mode=True)

        self.sfPlotWeight_ch2 = init_graph(self, self.gridLayout_ch2Graph,
                                           xtitle=SF_PLOT_XTITLE,
                                           xrange=SEC_FILED_XRANGE,
                                           yrange=SEC_FILED_YRANGE,
                                           disable_mouse=True,
                                           enable_legend=True,
                                           log_mode=True)

        self.sfPlotWeight_ch3 = init_graph(self, self.gridLayout_ch3Graph,
                                           xtitle=SF_PLOT_XTITLE,
                                           xrange=SEC_FILED_XRANGE,
                                           yrange=SEC_FILED_YRANGE,
                                           disable_mouse=True,
                                           enable_legend=True,
                                           log_mode=True)

        # history sec field graph
        self.sfPlotWeight_all_hist = init_graph(self, self.gridLayout_allGraph_hist,
                                                xtitle=REAL_TIME_PLOT_XTITLE,
                                                xrange=SEC_FILED_XRANGE,
                                                yrange=SEC_FILED_YRANGE,
                                                disable_mouse=True,
                                                enable_legend=True,
                                                log_mode=True)

        self.sfPlotWeight_ch1_hist = init_graph(self, self.gridLayout_allGraph_hist,
                                                xtitle=REAL_TIME_PLOT_XTITLE,
                                                xrange=SEC_FILED_XRANGE,
                                                yrange=SEC_FILED_YRANGE,
                                                disable_mouse=True,
                                                enable_legend=True,
                                                log_mode=True)

        self.sfPlotWeight_ch2_hist = init_graph(self, self.gridLayout_ch2Graph_hist,
                                                xtitle=REAL_TIME_PLOT_XTITLE,
                                                xrange=SEC_FILED_XRANGE,
                                                yrange=SEC_FILED_YRANGE,
                                                disable_mouse=True,
                                                enable_legend=True,
                                                log_mode=True)

        self.sfPlotWeight_ch3_hist = init_graph(self, self.gridLayout_ch3Graph_hist,
                                                xtitle=REAL_TIME_PLOT_XTITLE,
                                                xrange=SEC_FILED_XRANGE,
                                                yrange=SEC_FILED_YRANGE,
                                                disable_mouse=True,
                                                enable_legend=True,
                                                log_mode=True)

        # real time graph init
        self.rtPlotWeight_all = init_graph(self, self.gridLayout_allRealTime,
                                           xtitle=REAL_TIME_PLOT_XTITLE,
                                           xrange=REAL_TIME_PLOT_XRANGES,
                                           yrange=REAL_TIME_PLOT_YRANGES,
                                           disable_mouse=True,
                                           enable_legend=True)

        self.rtPlotWeight_ch1 = init_graph(self, self.gridLayout_ch1RealTime,
                                           xtitle=REAL_TIME_PLOT_XTITLE,
                                           xrange=REAL_TIME_PLOT_XRANGES,
                                           yrange=REAL_TIME_PLOT_YRANGES,
                                           disable_mouse=True,
                                           enable_legend=True)

        self.rtPlotWeight_ch2 = init_graph(self, self.gridLayout_ch2RealTime,
                                           xtitle=REAL_TIME_PLOT_XTITLE,
                                           xrange=REAL_TIME_PLOT_XRANGES,
                                           yrange=REAL_TIME_PLOT_YRANGES,
                                           disable_mouse=True,
                                           enable_legend=True)

        self.rtPlotWeight_ch3 = init_graph(self, self.gridLayout_ch3RealTime,
                                           xtitle=REAL_TIME_PLOT_XTITLE,
                                           xrange=REAL_TIME_PLOT_XRANGES,
                                           yrange=REAL_TIME_PLOT_YRANGES,
                                           disable_mouse=True,
                                           enable_legend=True)

        # history real time graph
        self.rtPlotWeight_all_hist = init_graph(self, self.gridLayout_allRealTime_hist,
                                                xtitle=REAL_TIME_PLOT_XTITLE,
                                                xrange=REAL_TIME_PLOT_XRANGES,
                                                yrange=REAL_TIME_PLOT_YRANGES,
                                                disable_mouse=False,
                                                enable_legend=True)

        self.rtPlotWeight_ch1_hist = init_graph(self, self.gridLayout_ch1RealTime_hist,
                                                xtitle=REAL_TIME_PLOT_XTITLE,
                                                xrange=REAL_TIME_PLOT_XRANGES,
                                                yrange=REAL_TIME_PLOT_YRANGES,
                                                disable_mouse=False,
                                                enable_legend=True)

        self.rtPlotWeight_ch2_hist = init_graph(self, self.gridLayout_ch2RealTime_hist,
                                                xtitle=REAL_TIME_PLOT_XTITLE,
                                                xrange=REAL_TIME_PLOT_XRANGES,
                                                yrange=REAL_TIME_PLOT_YRANGES,
                                                disable_mouse=False,
                                                enable_legend=True)

        self.rtPlotWeight_ch3_hist = init_graph(self, self.gridLayout_ch3RealTime_hist,
                                                xtitle=REAL_TIME_PLOT_XTITLE,
                                                xrange=REAL_TIME_PLOT_XRANGES,
                                                yrange=REAL_TIME_PLOT_YRANGES,
                                                disable_mouse=False,
                                                enable_legend=True)

        # channel data buffer (max size 2000)
        self.buf_realTime_ch1 = PlotBuf()
        self.buf_realTime_ch2 = PlotBuf()
        self.buf_realTime_ch3 = PlotBuf()

        dt, data = self.buf_realTime_ch1.getBuf()
        self.rtPlot_allch1_hist = self.rtPlotWeight_all_hist.plot(*data,
                                                                  name="CH1",
                                                                  pen=pg.mkPen(
                                                                      color=REAL_TIME_ALL_COLORS[0],
                                                                      width=REAL_TIME_LINE_WIDTH
                                                                  ))
        self.rtPlot_ch1_hist = self.rtPlotWeight_ch1_hist.plot(*data,
                                                               name="rt_CH1",
                                                               pen=pg.mkPen(
                                                                   color=REAL_TIME_LINE_COLOR,
                                                                   width=REAL_TIME_LINE_WIDTH
                                                               ))

        dt, data = self.buf_realTime_ch2.getBuf()
        self.rtPlot_allch2_hist = self.rtPlotWeight_all_hist.plot(*data,
                                                                  name="CH2",
                                                                  pen=pg.mkPen(
                                                                      color=REAL_TIME_ALL_COLORS[1],
                                                                      width=REAL_TIME_LINE_WIDTH
                                                                  ))
        self.rtPlot_ch2_hist = self.rtPlotWeight_ch2_hist.plot(*data,
                                                               name="rt_CH2",
                                                               pen=pg.mkPen(
                                                                   color=REAL_TIME_LINE_COLOR,
                                                                   width=REAL_TIME_LINE_WIDTH
                                                               ))

        dt, data = self.buf_realTime_ch3.getBuf()
        self.rtPlot_allch3_hist = self.rtPlotWeight_all_hist.plot(*data,
                                                                  name="CH3",
                                                                  pen=pg.mkPen(
                                                                      color=REAL_TIME_ALL_COLORS[2],
                                                                      width=REAL_TIME_LINE_WIDTH
                                                                  ))
        self.rtPlot_ch3_hist = self.rtPlotWeight_ch3_hist.plot(*data,
                                                               name="rt_CH3",
                                                               pen=pg.mkPen(
                                                                   color=REAL_TIME_LINE_COLOR,
                                                                   width=REAL_TIME_LINE_WIDTH
                                                               ))

        dt, data = self.buf_realTime_ch1.getBuf()
        self.rtPlot_allch1 = self.rtPlotWeight_all.plot(*data,
                                                        name="CH1",
                                                        pen=pg.mkPen(
                                                            color=REAL_TIME_ALL_COLORS[0],
                                                            width=REAL_TIME_LINE_WIDTH
                                                        ))
        self.rtPlot_ch1 = self.rtPlotWeight_ch1.plot(*data,
                                                     name="rt_CH1",
                                                     pen=pg.mkPen(
                                                         color=REAL_TIME_LINE_COLOR,
                                                         width=REAL_TIME_LINE_WIDTH
                                                     ))

        dt, data = self.buf_realTime_ch2.getBuf()
        self.rtPlot_allch2 = self.rtPlotWeight_all.plot(*data,
                                                        name="CH2",
                                                        pen=pg.mkPen(
                                                            color=REAL_TIME_ALL_COLORS[1],
                                                            width=REAL_TIME_LINE_WIDTH
                                                        ))
        self.rtPlot_ch2 = self.rtPlotWeight_ch2.plot(*data,
                                                     name="rt_CH2",
                                                     pen=pg.mkPen(
                                                         color=REAL_TIME_LINE_COLOR,
                                                         width=REAL_TIME_LINE_WIDTH
                                                     ))

        dt, data = self.buf_realTime_ch3.getBuf()
        self.rtPlot_allch3 = self.rtPlotWeight_all.plot(*data,
                                                        name="CH3",
                                                        pen=pg.mkPen(
                                                            color=REAL_TIME_ALL_COLORS[2],
                                                            width=REAL_TIME_LINE_WIDTH
                                                        ))
        self.rtPlot_ch3 = self.rtPlotWeight_ch3.plot(*data,
                                                     name="rt_CH3",
                                                     pen=pg.mkPen(
                                                         color=REAL_TIME_LINE_COLOR,
                                                         width=REAL_TIME_LINE_WIDTH
                                                     ))

        self.rtPlot_allch1.setDownsampling(auto=True)
        self.rtPlot_allch2.setDownsampling(auto=True)
        self.rtPlot_allch3.setDownsampling(auto=True)
        self.rtPlot_ch1.setDownsampling(auto=True)
        self.rtPlot_ch2.setDownsampling(auto=True)
        self.rtPlot_ch3.setDownsampling(auto=True)

        self.sfPlot_ch1_hist = self.sfPlotWeight_ch1_hist.plot(*data,
                                                               name="sf_CH1",
                                                               pen=pg.mkPen(
                                                                   color=REAL_TIME_LINE_COLOR,
                                                                   width=REAL_TIME_LINE_WIDTH
                                                               ))
        self.sfPlot_all_ch1_hist = self.sfPlotWeight_all_hist.plot(*data,
                                                                   name="CH1",
                                                                   pen=pg.mkPen(
                                                                       color=REAL_TIME_LINE_COLOR,
                                                                       width=REAL_TIME_LINE_WIDTH
                                                                   ))

        self.sfPlot_ch2_hist = self.sfPlotWeight_ch2_hist.plot(*data,
                                                               name="sf_CH2",
                                                               pen=pg.mkPen(
                                                                   color=REAL_TIME_LINE_COLOR,
                                                                   width=REAL_TIME_LINE_WIDTH
                                                               ))
        self.sfPlot_all_ch2_hist = self.sfPlotWeight_all_hist.plot(*data,
                                                                   name="CH2",
                                                                   pen=pg.mkPen(
                                                                       color=REAL_TIME_LINE_COLOR,
                                                                       width=REAL_TIME_LINE_WIDTH
                                                                   ))

        self.sfPlot_ch3_hist = self.sfPlotWeight_ch3_hist.plot(*data,
                                                               name="sf_CH3",
                                                               pen=pg.mkPen(
                                                                   color=REAL_TIME_LINE_COLOR,
                                                                   width=REAL_TIME_LINE_WIDTH
                                                               ))
        self.sfPlot_all_ch3_hist = self.sfPlotWeight_all_hist.plot(*data,
                                                                   name="CH3",
                                                                   pen=pg.mkPen(
                                                                       color=REAL_TIME_LINE_COLOR,
                                                                       width=REAL_TIME_LINE_WIDTH
                                                                   ))

        self.sfPlot_ch1 = self.sfPlotWeight_ch1.plot(*data,
                                                     name="sf_CH1",
                                                     pen=pg.mkPen(
                                                         color=REAL_TIME_LINE_COLOR,
                                                         width=REAL_TIME_LINE_WIDTH
                                                     ))
        self.sfPlot_all_ch1 = self.sfPlotWeight_all.plot(*data,
                                                         name="CH1",
                                                         pen=pg.mkPen(
                                                             color=REAL_TIME_ALL_COLORS[0],
                                                             width=REAL_TIME_LINE_WIDTH
                                                         ))

        self.sfPlot_ch2 = self.sfPlotWeight_ch2.plot(*data,
                                                     name="sf_CH2",
                                                     pen=pg.mkPen(
                                                         color=REAL_TIME_LINE_COLOR,
                                                         width=REAL_TIME_LINE_WIDTH
                                                     ))
        self.sfPlot_all_ch2 = self.sfPlotWeight_all.plot(*data,
                                                         name="CH2",
                                                         pen=pg.mkPen(
                                                             color=REAL_TIME_ALL_COLORS[1],
                                                             width=REAL_TIME_LINE_WIDTH
                                                         ))

        self.sfPlot_ch3 = self.sfPlotWeight_ch3.plot(*data,
                                                     name="sf_CH3",
                                                     pen=pg.mkPen(
                                                         color=REAL_TIME_LINE_COLOR,
                                                         width=REAL_TIME_LINE_WIDTH
                                                     ))
        self.sfPlot_all_ch3 = self.sfPlotWeight_all.plot(*data,
                                                         name="CH3",
                                                         pen=pg.mkPen(
                                                             color=REAL_TIME_ALL_COLORS[2],
                                                             width=REAL_TIME_LINE_WIDTH
                                                         ))

        self.real_time_graph_updater = MainGraphUpdaterThread(self)
        self.sec_time_graph_updater = SecGraphUpdaterThread(self)

        self.rtGraph_Ticker = QTimer()
        self.rtGraph_Ticker.timeout.connect(self.doUpdateRealTimeGraph)

        self.sfGraph_Ticker = QTimer()
        self.sfGraph_Ticker.timeout.connect(self.doUpdateSecFieldGraph)

        # initialize filename indicator
        self.label_titleFilenameHeader.setVisible(False)
        self.label_filenameHeader_2.setVisible(False)

        # FPGA communication
        self.fpga_com = None
        self.fpga_ctl = None

        # self.fpga_com.start()

        # GPS communication
        self.gps_error_count = 0

        self.gps_updater = GPSUpdaterThread(self)

        self.gps_Ticker = QTimer()
        self.gps_Ticker.timeout.connect(self.doUpdateGPSandSDCardSpace)
        self.gps_Ticker.start(1000)

        # data updater
        self.data_updater = DataUpdaterThread(self)

        self.data_Ticker = QTimer()
        self.data_Ticker.timeout.connect(self.doUpdateData)

        # controls of serial to parallel chips
        self.bandwidth_ctl = None
        self.amp_ctl = None

        # initialized signal
        # self.amp_ctl.set_LED(True, True, True, True)

        # timer
        self.record_start_ts = 0

    def staticGenerateFilename(self) -> str:
        time_text = time.strftime("%Y%m%d_%H%M%S", self.gps_updater.gps.get_realtime())
        ret = f"{time_text}_{self.comboBox_radiateFreq.currentText()}_{self.comboBox_sampleRate.currentText()}"
        return ret

    def onButtonSwitchToRealTimeClicked(self):
        self.stackedWidget_topBar.setCurrentIndex(0)
        self.stackedWidget_allGraph.setCurrentIndex(0)
        self.stackedWidget_ch1Graph.setCurrentIndex(0)
        self.stackedWidget_ch2Graph.setCurrentIndex(0)
        self.stackedWidget_ch3Graph.setCurrentIndex(0)

        self.stackedWidget_topBar_hist.setCurrentIndex(0)
        self.stackedWidget_allGraph_hist.setCurrentIndex(0)
        self.stackedWidget_ch1Graph_hist.setCurrentIndex(0)
        self.stackedWidget_ch2Graph_hist.setCurrentIndex(0)
        self.stackedWidget_ch3Graph_hist.setCurrentIndex(0)

    def onButtonSwitchToSecFieldClicked(self):
        self.stackedWidget_topBar.setCurrentIndex(1)
        self.stackedWidget_allGraph.setCurrentIndex(1)
        self.stackedWidget_ch1Graph.setCurrentIndex(1)
        self.stackedWidget_ch2Graph.setCurrentIndex(1)
        self.stackedWidget_ch3Graph.setCurrentIndex(1)

        self.stackedWidget_topBar_hist.setCurrentIndex(1)
        self.stackedWidget_allGraph_hist.setCurrentIndex(1)
        self.stackedWidget_ch1Graph_hist.setCurrentIndex(1)
        self.stackedWidget_ch2Graph_hist.setCurrentIndex(1)
        self.stackedWidget_ch3Graph_hist.setCurrentIndex(1)

    def onButtonStartRecordClicked(self):
        if self.toolButton_startRecording.isChecked():
            self.stackedWidget_mainGraph.setCurrentIndex(1)
            self.toolButton_settings.setVisible(True)
            self.actionStartRecording()
        else:
            self.actionStopRecording()

    def onButtonSettingClicked(self):
        if not self.flag_recording:
            self.stackedWidget_mainGraph.setCurrentIndex(0)
            self.toolButton_settings.setVisible(False)

    def onButtonReturnToMenuClicked(self):
        self.stackedWidget_menu.setCurrentIndex(0)

    def onButtonGTEMClicked(self):
        self.stackedWidget_menu.setCurrentIndex(1)

    def onButtonHistoryClicked(self):
        self.stackedWidget_menu.setCurrentIndex(2)

    def actionStartRecording(self):
        self.doResetRealTimeGraph()
        self.rtGraph_Ticker.start(500)
        self.sfGraph_Ticker.start(1000)
        self.toolButton_startRecording.setText("正在采集")
        self.toolButton_settings.setEnabled(False)
        self.toolButton_mainMenu.setEnabled(False)
        self.flag_recording = True

        # set init timestamp
        self.record_start_ts = time.time()

        # reset buffer
        self.buf_realTime_ch1.reset(25000 * 5, sample_rate=int(self.comboBox_sampleRate.currentText()),
                                    freq=float(self.comboBox_radiateFreq.currentText()))
        self.buf_realTime_ch2.reset(25000 * 5, sample_rate=int(self.comboBox_sampleRate.currentText()),
                                    freq=float(self.comboBox_radiateFreq.currentText()))
        self.buf_realTime_ch3.reset(25000 * 5, sample_rate=int(self.comboBox_sampleRate.currentText()),
                                    freq=float(self.comboBox_radiateFreq.currentText()))

        # reset graphs
        self.rtPlotWeight_all.setLimits(xMin=-10, xMax=5)
        self.rtPlotWeight_all.setXRange(*REAL_TIME_PLOT_XRANGES)
        self.rtPlotWeight_ch1.setLimits(xMin=-10, xMax=5)
        self.rtPlotWeight_ch1.setXRange(*REAL_TIME_PLOT_XRANGES)
        self.rtPlotWeight_ch2.setLimits(xMin=-10, xMax=5)
        self.rtPlotWeight_ch2.setXRange(*REAL_TIME_PLOT_XRANGES)
        self.rtPlotWeight_ch3.setLimits(xMin=-10, xMax=5)
        self.rtPlotWeight_ch3.setXRange(*REAL_TIME_PLOT_XRANGES)

        # load FPGA configuration
        # self.fpga_ctl.enable_channels(self.comboBox_ch1BandWidth.currentText() != '闭合',
        #                               self.comboBox_ch2BandWidth.currentText() != '闭合',
        #                               self.comboBox_ch3BandWidth.currentText() != '闭合')
        # self.fpga_ctl.set_sample_rate_level(self.comboBox_sampleRate.currentIndex())
        # self.fpga_ctl.set_amp_rate_of_channels(self.comboBox_ch1Amp.currentText(),
        #                                        self.comboBox_ch2Amp.currentText(),
        #                                        self.comboBox_ch3Amp.currentText())

        # load filename
        filename = self.staticGenerateFilename()
        abs_path = f"{MOUNT_PATH}/{filename}.bin"
        # print("SPI DEV status before file open: {}".format(self.fpga_com.mp_status))
        # self.fpga_com.set_output_file(abs_path)

        # start FPGA
        # self.fpga_com.open()
        # self.fpga_ctl.start_FPGA()

        # set amp rate
        # self.amp_ctl.set_amp_rate(
        #     self.comboBox_ch1Amp.currentText(),
        #     self.comboBox_ch2Amp.currentText(),
        #     self.comboBox_ch3Amp.currentText(),
        #     update=False
        # )
        # self.amp_ctl.set_LED(False, False, False, False, update=True)

        # set bandwidth
        # self.bandwidth_ctl.set_bandwidth(
        #     self.comboBox_ch1BandWidth.currentText(),
        #     self.comboBox_ch2BandWidth.currentText(),
        #     self.comboBox_ch3BandWidth.currentText(),
        # )

        # update filename display
        self.label_titleFilenameHeader.setVisible(True)
        self.label_titleFilenameHeader.setText("写入：")
        self.doUpdateFilenameHeader(f"{filename}.bin")

        # enable gps_save
        abs_path = f"{MOUNT_PATH}/{filename}_gps.txt"
        self.gps_updater.gps.set_gps_file(abs_path)
        self.gps_updater.gps.enable_gps_dump(True)

        # start data updater
        self.data_updater.reset()
        self.data_Ticker.start(2)

    def actionStopRecording(self):
        self.rtGraph_Ticker.stop()
        self.sfGraph_Ticker.stop()
        self.toolButton_startRecording.setText("开始采集")
        self.toolButton_settings.setEnabled(True)
        self.toolButton_mainMenu.setEnabled(True)
        self.flag_recording = False

        # stop FPGA
        # self.fpga_com.close()
        # self.fpga_ctl.stop_FPGA()

        # stop data update
        self.data_Ticker.stop()

        # update saved filename
        self.label_titleFilenameHeader.setText("已保存：")

        # stop gps dump
        self.gps_updater.gps.enable_gps_dump(False)

        # reset timer
        self.record_start_ts = 0.0
        ta = time.localtime(0.0)
        time_str = time.strftime("%H:%M:%S", ta)
        self.label_recordedTime_2.setText(time_str)

    def actionSelectHistoryFile(self):
        filename = QFileDialog.getOpenFileName(caption="打开",
                                               filter="二进制文件 (*.bin);;"
                                                      "所有文件类型 (*)",
                                               parent=self)[0]
        self.history_file = Gtem24File(filename)
        self.label_historyFilename.setText(DirTree(filename).name)
        self.doUpdateSfGraph()

    def doUpdateSfGraph(self):
        add_time = int(self.comboBox_secFieldStackingTime_hist.currentText())
        x, sig = self.history_file.gateTraceSecFieldExtract(add_time)
        self.sfPlot_all_ch1_hist.setData(x, sig)
        self.sfPlot_ch1_hist.setData(x, sig)

    def doUpdateHistoryRtGraph(self):
        pass

    def doUpdateGPSandSDCardSpace(self):
        self.gps_updater.start()

        # detect SD card
        # def decode_df(msg: str) -> float:
        #     msg = msg.split(" ")
        #     while "" in msg:
        #         msg.remove("")
        #     total = int(msg[1])
        #     free = int(msg[3])
        #     return free * 100 / total
        #
        # if os.path.exists(SD_PATH):
        #     p = os.popen("df")
        #     data = p.readlines()
        #     p.close()
        #     data = data[1:]
        #     value = -1
        #     for ele in data:
        #         if SD_PATH in ele:
        #             value = decode_df(ele)
        #
        #     if value == -1:
        #         os.system(f"sudo mount {SD_PATH} {MOUNT_PATH}")
        #         p = os.popen("df")
        #         data = p.readlines()
        #         p.close()
        #         value = -1
        #         for ele in data:
        #             if SD_PATH in ele:
        #                 value = decode_df(ele)
        #
        #     self.progressBar.setEnabled(True)
        #     self.progressBar.setValue(int(value))
        #     self.toolButton_startRecording.setEnabled(True)
        # else:
        #     if self.flag_recording:
        #         self.actionStopRecording()
        #     self.progressBar.setEnabled(False)
        #     self.toolButton_startRecording.setEnabled(False)
        #
        # # update GPS
        # if self.gps_updater.gps_status:
        #     self.toolButton_startRecording.setEnabled(True)
        #     self.gps_error_count = 0
        # else:
        #     if self.gps_error_count > 3:
        #         if self.flag_recording:
        #             self.actionStopRecording()
        #         self.toolButton_startRecording.setEnabled(False)
        #     else:
        #         self.gps_error_count += 1
        #
        # # update timer
        # if self.flag_recording:
        #     ta = time.localtime(time.time() - self.record_start_ts)
        #     time_str = time.strftime("%H:%M:%S", ta)
        #     self.label_recordedTime_2.setText(time_str)
        self.toolButton_startRecording.setEnabled(True)

    def doUpdateFilenameHeader(self, value):
        self.label_filenameHeader_2.setVisible(True)
        self.label_filenameHeader_2.setText("\"{}\"".format(value))

    def doUpdateData(self):
        self.data_updater.start()

    def doUpdateBattery(self, value):
        self.label_batteryRemains_2.setText("{}%".format(value))

    def doResetRealTimeGraph(self):
        sample_rate = int(self.comboBox_sampleRate.currentText())
        emit_rate = int(self.comboBox_radiateFreq.currentText())
        self.buf_realTime_ch1.reset(MAX_BUFFER_TIME * sample_rate, sample_rate, freq=emit_rate)
        self.buf_realTime_ch2.reset(MAX_BUFFER_TIME * sample_rate, sample_rate, freq=emit_rate)
        self.buf_realTime_ch3.reset(MAX_BUFFER_TIME * sample_rate, sample_rate, freq=emit_rate)

        dt, data = self.buf_realTime_ch1.getBuf()
        self.rtPlotWeight_ch1.setLimits(xMin=data[0][0], xMax=data[0][-1])
        self.rtPlot_ch1.setData(*data)
        self.rtPlotWeight_ch1.setRange(xRange=REAL_TIME_PLOT_XRANGES, padding=0)
        dt, data = self.buf_realTime_ch2.getBuf()
        self.rtPlotWeight_ch2.setLimits(xMin=data[0][0], xMax=data[0][-1])
        self.rtPlot_ch2.setData(*data)
        self.rtPlotWeight_ch2.setRange(xRange=REAL_TIME_PLOT_XRANGES, padding=0)
        dt, data = self.buf_realTime_ch3.getBuf()
        self.rtPlotWeight_ch3.setLimits(xMin=data[0][0], xMax=data[0][-1])
        self.rtPlot_ch3.setData(*data)
        self.rtPlotWeight_ch3.setRange(xRange=REAL_TIME_PLOT_XRANGES, padding=0)

    def doUpdateRealTimeGraph(self):

        # blink LED
        # self.amp_ctl.set_LED(not self.amp_ctl.leds[0])

        if self.stackedWidget_topBar.currentIndex() != 0 or self.real_time_graph_updater.isRunning():
            return

        if self.real_time_graph_updater.isFinished():
            self.real_time_graph_updater.update_graph()

        self.real_time_graph_updater.start()
        # sample_rate = int(self.comboBox_sampleRate.currentText())
        # emit_rate = int(self.comboBox_radiateFreq.currentText())
        # tab_index = self.tabWidget_channelGraph.currentIndex()
        # current_buf = None
        # current_data = None
        #
        # if tab_index == 1:
        #     current_buf = self.buf_realTime_ch1
        #     current_plot = self.rtPlotWeight_ch1
        #     current_data = self.rtPlot_ch1
        # elif tab_index == 2:
        #     current_buf = self.buf_realTime_ch2
        #     current_plot = self.rtPlotWeight_ch2
        #     current_data = self.rtPlot_ch2
        # elif tab_index == 3:
        #     current_buf = self.buf_realTime_ch3
        #     current_plot = self.rtPlotWeight_ch3
        #     current_data = self.rtPlot_ch3
        # else:
        #     current_plot = self.rtPlotWeight_all
        #
        # max_view_range = 4 / emit_rate
        # view_range = int(max_view_range * sample_rate)
        #
        # if tab_index:
        #     dt, data = current_buf.getBuf(view_range)
        #     x_range = current_plot.getViewBox().viewRange()
        #     y_range = x_range[1]
        #     x_range = x_range[0]
        #     x_start = (x_range[0] + dt) * max_view_range // max_view_range
        #     x_range = [x_start, x_start + max_view_range]
        #
        #     current_data.setData(*data)
        # else:
        #     dt, data = self.buf_realTime_ch1.getBuf(view_range)
        #     x_range = current_plot.getViewBox().viewRange()
        #     y_range = x_range[1]
        #     x_range = x_range[0]
        #     x_range = [x_range[0] + dt, x_range[1] + dt]
        #     self.rtPlot_allch1.setData(*data)
        #     dt, data = self.buf_realTime_ch2.getBuf(view_range)
        #     self.rtPlot_allch2.setData(*data)
        #     dt, data = self.buf_realTime_ch3.getBuf(view_range)
        #     self.rtPlot_allch3.setData(*data)
        #
        # xmin = data[0][0]
        #
        # self.rtPlotWeight_all.setLimits(xMin=xmin, xMax=data[0][-1])
        # self.rtPlotWeight_all.setRange(xRange=x_range, yRange=y_range, padding=0)
        # self.rtPlotWeight_ch1.setLimits(xMin=xmin, xMax=data[0][-1])
        # self.rtPlotWeight_ch1.setRange(xRange=x_range, yRange=y_range, padding=0)
        # self.rtPlotWeight_ch2.setLimits(xMin=xmin, xMax=data[0][-1])
        # self.rtPlotWeight_ch2.setRange(xRange=x_range, yRange=y_range, padding=0)
        # self.rtPlotWeight_ch3.setLimits(xMin=xmin, xMax=data[0][-1])
        # self.rtPlotWeight_ch3.setRange(xRange=x_range, yRange=y_range, padding=0)

    def doUpdateSecFieldGraph(self):
        if self.stackedWidget_topBar.currentIndex() != 1 or self.sec_time_graph_updater.isRunning():
            return

        if self.sec_time_graph_updater.isFinished():
            self.sec_time_graph_updater.update_graph()
        self.sec_time_graph_updater.start()
        # add_time = int(self.comboBox_secFieldStackingTime.currentText())
        # sample_rate = int(self.comboBox_sampleRate.currentText())
        # emit_rate = int(self.comboBox_radiateFreq.currentText())
        # tab_index = self.tabWidget_channelGraph.currentIndex()
        # current_buf = None
        # current_data = None
        #
        # if tab_index == 1:
        #     current_buf = self.buf_realTime_ch1
        #     current_data = self.sfPlot_ch1
        #     data = current_buf.getBuf(sample_rate * add_time)
        #     x, sig = Gtem24(sample_rate=sample_rate,
        #                     emit_freq=emit_rate,
        #                     data=data[1][1]).gateTraceSecFieldExtract(add_time)
        #     current_data.setData(x, sig)
        #
        # elif tab_index == 2:
        #     current_buf = self.buf_realTime_ch2
        #     current_data = self.sfPlot_ch2
        #     data = current_buf.getBuf(sample_rate * add_time)
        #     x, sig = Gtem24(sample_rate=sample_rate,
        #                     emit_freq=emit_rate,
        #                     data=data[1][1]).gateTraceSecFieldExtract(add_time)
        #     current_data.setData(x, sig)
        # elif tab_index == 3:
        #     current_buf = self.buf_realTime_ch3
        #     current_data = self.sfPlot_ch3
        #     data = current_buf.getBuf(sample_rate * add_time)
        #     x, sig = Gtem24(sample_rate=sample_rate,
        #                     emit_freq=emit_rate,
        #                     data=data[1][1]).gateTraceSecFieldExtract(add_time)
        #     current_data.setData(x, sig)
        # else:
        #     current_plot = self.rtPlotWeight_all
        #     current_data = self.rtPlot_ch1


def test(ui):
    cnt = 0
    batch_size = int(int(ui.comboBox_sampleRate.currentText()) / int(ui.comboBox_radiateFreq.currentText()))
    dt = batch_size / int(ui.comboBox_sampleRate.currentText())
    dt_i = 1 / int(ui.comboBox_sampleRate.currentText())
    ti = 0
    t0 = time.time()
    gt = Gtem24File("../sample/GTEM_tests/dataTEM1/220102_100601.bin")
    live = True

    print("batch size: {}".format(batch_size))

    def test(ti, cnt, ui):
        while live:
            t1_0 = time.time()
            for i in range(batch_size):
                ti += dt_i
                cnt += 1
                try:
                    ui.buf_realTime_ch1.updateBatch(gt[cnt:cnt + 4000], ti)
                except:
                    cnt = 0

            delay = dt - time.time() + t1_0
            if delay < 0:
                print("warning: can not keep up, delayed behind for {:.3f}ms".format(-delay * 1000))
            else:
                time.sleep(delay)

    t = threading.Thread(target=test, args=(ti, cnt, ui))
    t.start()
    return t


if __name__ == '__main__':
    global ti, cnt
    app = QApplication(sys.argv)
    ui = UIReceiver()

    if TEST:
        # t = test(ui)  # self loopback test
        ui.flag_debug = True

    ui.showMaximized()
    extco = app.exec_()
    live = False

    # ui.fpga_com.kill()

    # if TEST:
    #     t.join()
    sys.exit(extco)
