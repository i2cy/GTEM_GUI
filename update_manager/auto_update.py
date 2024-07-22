#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: System_Installation.md
# Filename: auto_update
# Created on: 2024/7/9

from i2ftps.client import I2ftpClient
from i2cylib.utils.logger import Logger
import json

LOGGER = Logger()

def main():
    clt = I2ftpClient()

