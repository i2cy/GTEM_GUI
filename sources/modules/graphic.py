#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: graphic
# Created on: 2023/2/12


import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QSizePolicy


def init_graph(app, layout, xtitle, xrange, yrange, disable_mouse=False, enable_legend=True, log_mode=False):
    plot_weight = pg.PlotWidget()
    sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(app.centralwidget.sizePolicy().hasHeightForWidth())
    plot_weight.setSizePolicy(sizePolicy)
    plot_weight.plotItem.setLabels(bottom=xtitle)
    plot_weight.plotItem.showGrid(x=True, y=True, alpha=0.5)
    plot_weight.plotItem.showAxes("top")
    plot_weight.plotItem.showAxes("right")
    if log_mode:
        plot_weight.plotItem.setLogMode(x=True, y=True)
    if enable_legend:
        plot_weight.plotItem.addLegend()
    if disable_mouse:
        plot_weight.setMouseEnabled(False, False)
    plot_weight.setXRange(*xrange)
    plot_weight.setYRange(*yrange)
    layout.addWidget(plot_weight)
    app.setLayout(layout)

    return plot_weight
