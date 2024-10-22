#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: System_Installation.md
# Filename: networking
# Created on: 2024/9/4

"""
this is an unsafe module which must only use in local network

communication process after TCP connection is established:
 1. server --(16B random key)-> client
 2. client --(hashed validation key)-> server
 3. server --(protocol version string)-> client
 4. double side communication...(custom package format)

custom package format (big endian):
--------------------------------------------------------
    offset  |   typing   |  name    |   notes
--------------------------------------------------------
    0           uint8       cmd         package type ID
    1           uint32      length      payload length
    5           raw         payload     content
"""

import struct
import socket
import random
import threading
import time
from hashlib import md5, sha256

from i2cylib.utils.logger import Logger

VERSION = "0.0.1"


def rand_key_gen_16B():
    """
    generate a 16B random key
    :return:
    """
    return random.randbytes(16)


def pak_encode(cmd_id: int, payload: bytes):
    """
    pack payload for TCP connection
    :param cmd_id: 0-client configuration(Amp. rate, Bandwidth) command, 1-client filename set command, 2-
    :param payload:
    :return:
    """
    length = len(payload)
    ret = struct.pack(">BI", cmd_id, length) + payload
    return ret


def pak_header_decode(raw: bytes):
    """
    unpack payload from raw bytes
    :param raw:
    :return: cmd_id, payload_length
    """
    cmd_id, length = struct.unpack(">BI", raw[:5])
    return cmd_id, length


class Auther:

    def __init__(self, psk: bytes):
        """
        authenticator
        :param psk:
        """
        self.psk = psk

    def sign(self, key: bytes):
        """
        make signature with given key
        :param key: 16B random array
        :return:
        """
        hasher = md5()
        hasher.update(sha256(self.psk + key + b"26580").digest())
        return hasher.digest()[:16]

    def check(self, key: bytes, signature: bytes):
        """
        verify signature with given key
        :param key: 16B random array
        :param signature: 16B signature
        :return:
        """
        a = self.sign(key)
        return a == signature


class Server:

    def __init__(self, port=2565, listen="0.0.0.0", psk=b"n1c2n3_89n96sdgi", logger: Logger = None):
        """
        initialize an instance of GTEM Server
        :param port: listen port (default 2565)
        :param listen: listening address (default 0.0.0.0)
        """

        if logger is None:
            # create new logger if not set
            logger = Logger()
        self.__logger = logger

        self.port = port
        self.listening = listen
        self.connections = []
        self.live = False
        self.threads = []

        # init auther
        self.auther = Auther(psk)

        # build socket
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.bind((self.listening, self.port))

    def start(self):
        """
        start the server
        :return:
        """
        self.__logger.INFO(f"[Server] starting GTEM data server at {self.listening}:{self.port}")
        self.srv.listen(5)
        self.threads.append(threading.Thread(target=self.__thr_con_accept, daemon=True))
        self.threads.append(threading.Thread(target=self.__thr_handler, daemon=True))
        self.live = True
        [ele.start() for ele in self.threads]

    def kill(self):
        """
        kill all threads and close server
        :return:
        """
        self.__logger.INFO("[Server] kill all threads and close server")
        self.live = False
        time.sleep(0.5)

        [ele.join() for ele in self.threads]
        self.threads = []

    def __auth(self, con: socket.socket):
        """
        authenticate with client
        :param con: socket
        :return:
        """
        # send 16B random key to client
        key = rand_key_gen_16B()  # generate random key
        try:
            con.sendall(key)
        except socket.error:
            return False  # exit if connection failed

        # receiving signature from client
        signature = con.recv(16)
        err_cnt = 0
        while len(signature) < 16:
            signature += con.recv(16 - len(signature))
            err_cnt += 1
            if err_cnt > 10:
                return False  # break if signature failed to retrieve or bad response (after 10 tries)

        # checking signature
        return self.auther.check(key, signature)

    def __thr_con_accept(self):
        """
        handling incoming connection
        :return:
        """
        self.__logger.DEBUG("[Server] [con_accept] thread started")

        while self.live:
            try:
                conn, addr = self.srv.accept()
                self.connections.append((conn, addr))
            except socket.error as err:
                self.__logger.WARNING(f"[Server] [con_accept] socket error: {err}")

        self.__logger.DEBUG("[Server] [con_accept] thread stopped")



    def __thr_handler(self):
        """
        handling connections: receiving commands, sending data
        :return:
        """
