#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: 9.3 地面接收机软件
# Filename: install
# Created on: 2023/4/22

import os

mod_20 = """Section "Device"
    Identifier  "Rockchip Graphics"
    Driver      "modesetting"

### Use Rockchip RGA 2D HW accel
#    Option      "AccelMethod"    "exa"

### Use GPU HW accel
    Option      "AccelMethod"    "glamor"

    Option      "DRI"            "2"

### Set to "none" to avoid tearing, could lead to up 50% performance loss
    Option      "FlipFB"         "none"

### Limit flip rate and drop frames for "FlipFB" to reduce performance lost
#    Option      "MaxFlipRate"    "60"

    Option      "NoEDID"         "true"
    Option      "UseGammaLUT"    "true"
EndSection

Section "Screen"
    Identifier  "Default Screen"
    Device      "Rockchip Graphics"
    Monitor     "Default Monitor"
EndSection

### Valid values for rotation are "normal", "left", "right"
Section "Monitor"
    Identifier  "Default Monitor"
    Option      "Rotate" "right"
EndSection"""

mod_40 = """# Match on all types of devices but joysticks
#
# If you want to configure your devices, do not copy this file.
# Instead, use a config snippet that contains something like this:
#
# Section "InputClass"
#   Identifier "something or other"
#   MatchDriver "libinput"
#
#   MatchIsTouchpad "on"
#   ... other Match directives ...
#   Option "someoption" "value"
# EndSection
#
# This applies the option any libinput device also matched by the other
# directives. See the xorg.conf(5) man page for more info on
# matching devices.
 
Section "InputClass"
        Identifier "libinput pointer catchall"
        MatchIsPointer "on"
        MatchDevicePath "/dev/input/event*"
        Driver "libinput"
EndSection
 
Section "InputClass"
        Identifier "libinput keyboard catchall"
        MatchIsKeyboard "on"
        MatchDevicePath "/dev/input/event*"
        Driver "libinput"
EndSection
 
Section "InputClass"
        Identifier "libinput touchpad catchall"
        MatchIsTouchpad "on"
        MatchDevicePath "/dev/input/event*"
        Driver "libinput"
EndSection
 
Section "InputClass"
        Identifier "libinput touchscreen catchall"
        MatchIsTouchscreen "on"
        MatchDevicePath "/dev/input/event*"
        Option "TransformationMatrix" "0 1 0 -1 0 1 0 0 1"
        Driver "libinput"
EndSection
 
Section "InputClass"
        Identifier "libinput tablet catchall"
        MatchIsTablet "on"
        MatchDevicePath "/dev/input/event*"
        Driver "libinput"
EndSection"""

if __name__ == '__main__':
    # install python3 dev
    print("## Installing Python3 development environment and GCC toolkit")
    os.system("sudo apt update && sudo apt install -y python3-pip python3-pyqt5 python3-dev gcc nano")
    # upgrade pip
    print("## upgrading Python3 Pip")
    os.system("pip install -U pip")
    # install requirements.txt
    print("## Installing requirements for GTEM")
    os.system("pip install -r requirements.txt")
    # rotating screen
    print("## Rotating screen")
    with open("/etc/X11/xorg.conf.d/20-modesetting.conf", "w") as f:
        f.write(mod_20)
        f.close()
    print("## Rotating input vector of screen")
    with open("/usr/share/X11/xorg.conf.d/40-libinput.conf", "w") as f:
        f.write(mod_40)
        f.close()

    print("## Done")
