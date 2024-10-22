#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: System_Installation.md
# Filename: backend
# Created on: 2024/8/23

from ch347api.spi import SPIDevice, SPIClockFreq
import struct
import socket
from modules.i2c import FPGACtl, AmpRateCtl, BandWidthCtl, FPGAStatusStruct

# SPI settings
SPI_SPEED = SPIClockFreq.f_30M
SPI_MODE = 0


class GTEMBackendServer:
    """
    backend server of GTEM, including features:
    1. communication with data_processor process client
    2. communication with display and control client
    """

    def __init__(self, port: int = 17743):
        """
        initialize backend server.
        :param port: server port that listening
        :type port: int
        """


