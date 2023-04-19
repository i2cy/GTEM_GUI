1. 更新apt源到bullseye并使用apt安装

   `apt install python3-pip python3-pyqt5 python3-dev gcc nano`

2. 部署FRPC客户端，启动项`/etc/systemd/system/frpc.service`

       [Unit]
       Description=Frp Client Service
       After=network.target
         
       [Service]
       User=root
       Group=root
       Type=simple
       DynamicUser=true
       Restart=on-failure
       RestartSec=5s
       ExecStart=/usr/bin/frpc -c /etc/frp/frpc.ini
       ExecReload=/usr/bin/frpc reload -c /etc/frp/frpc.ini
       LimitNOFILE=1048576
       CPUSchedulingPolicy=rr
       CPUSchedulingPriority=3
       
       [Install]
       WantedBy=multi-user.target
       Alias=frpc.service

3. 拷贝源码
4. 更新pip

   `pip install -U pip`

5. 安装requirements.txt

   `pip install -r requirements.txt`

6. 修改`/etc/X11/xorg.conf.d/20-modesetting.conf`为以下内容，旋转屏幕

       Section "Device"
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
       EndSection

7. 修改`/usr/share/X11/xorg.conf.d/40-libinput.conf`为以下内容，旋转输入矩阵

       # Match on all types of devices but joysticks
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
       EndSection