1. 部署FRPC客户端
2. 安装nano
3. 拷贝源码
4. 更新apt源到bullseye
5. 使用apt安装pip、PyQt5(use --fix-missing)
6. 更新pip
7. 安装requirements.txt
8. 使用如下命令安装wiringpi for Rk3399

       apt install git python-dev python-setuptools python3-dev python3-setuptools swig
       wget https://pypi.io/packages/source/s/setuptools/setuptools-33.1.1.zip
       unzip setuptools-33.1.1.zip
       cd setuptools-33.1.1
       python3 setup.py install
       wget http://112.124.9.243:8888/wiringpi/friendlyelec-rk3399/wiringpi-2.44.4-py3.6-linux-aarch64.egg
       easy_install wiringpi-2.44.4-py3.6-linux-aarch64.egg
9. 