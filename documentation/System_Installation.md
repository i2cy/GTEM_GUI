1. ����FRPC�ͻ���
2. ��װnano
3. ����Դ��
4. ����aptԴ��bullseye
5. ʹ��apt��װpip��PyQt5(use --fix-missing)
6. ����pip
7. ��װrequirements.txt
8. ʹ���������װwiringpi for Rk3399

       apt install git python-dev python-setuptools python3-dev python3-setuptools swig
       wget https://pypi.io/packages/source/s/setuptools/setuptools-33.1.1.zip
       unzip setuptools-33.1.1.zip
       cd setuptools-33.1.1
       python3 setup.py install
       wget http://112.124.9.243:8888/wiringpi/friendlyelec-rk3399/wiringpi-2.44.4-py3.6-linux-aarch64.egg
       easy_install wiringpi-2.44.4-py3.6-linux-aarch64.egg
9. 