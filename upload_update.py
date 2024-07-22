#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: System_Installation.md
# Filename: upload_update
# Created on: 2024/7/8

import os
import time
from i2ftps.client import I2ftpClient
from i2cylib.utils.logger import Logger
import json

LOGGER = Logger(level="INFO")
update_packs_cache = "uploads"
config_path = "update_manager/updater_conf.json"
server_side_path = "gtem_updates"


def main():
    # pack all files
    LOGGER.DEBUG("[Uploader] preparing source pack")
    pack_name = "gtem_{}.txz".format(int(time.time()))
    pack_local_path = "{}/{}".format(update_packs_cache, pack_name)
    pack_cloud_path = "{}/{}".format(server_side_path, pack_name)
    os.system("tar --xz -cf {} sources >nul".format(pack_local_path))
    LOGGER.INFO("[Uploader] generated update pack: {}".format(pack_local_path))
    # load configs
    LOGGER.DEBUG("[Uploader] loading configuration about update server")
    with open(config_path) as f:
        conf = json.load(f)
    # connect to server
    LOGGER.INFO("[Uploader] establishing connection to update server")
    clt = I2ftpClient(conf["hostname"], port=conf["port"], key=bytes.fromhex(conf["keychain"]),
                      logger=Logger)
    status, ret = clt.connect(timeout=5)
    if not status:
        LOGGER.ERROR("[Uploader] failed to establish connection with update server at {}:{}".format(
            conf["hostname"], conf["port"]
        ))
        return  # abort upload
    status, response = clt.list(server_side_path)
    if status:
        LOGGER.INFO("[Uploader] {} updates available on server".format(len(response)))
    else:
        LOGGER.WARNING("[Uploader] failed to get list of updates from server, {}".format(
            response
        ))
        clt.mkdir(server_side_path)

    # upload update pack to server
    LOGGER.INFO("[Uploader] uploading files to server")
    while True:
        status, ret = clt.upload(pack_cloud_path)
        if not status:
            LOGGER.ERROR("[Uploader] failed to upload update pack to server, {}".format(ret))
            clt.disconnect()
            return  # abort
        LOGGER.echo = False  # make sure upload process bar is clear to view
        ret.upload(pack_local_path, close_session_when_finished=False)
        LOGGER.echo = True
        verify_res = ret.verify()
        if not verify_res:
            LOGGER.ERROR("failed to verify cloud file hash, update pack may be corrupted during uploading, retrying")
        else:
            break

    clt.disconnect()
    LOGGER.INFO("[Uploader] upload complete")


if __name__ == '__main__':
    main()
