# 用户手册：SPI数据完整性测试

## 测试前准备（RK3399）

1. 搭建WIFI热点

    - 确保自己的手机能够访问互联网后，开启手机热点，并将手机热点网络名称（SSID）修改为`GTEM_BRIDGE`,密码设置为`gtembridge001`。
    - 设备开机完成后会自动连接这个热点（如下图）
    
    <div align="center"><img width="200" src="https://pan.i2cy.tech/f/6JHy/Screenshot_20240322_150856_com.android.settings.jpg"/></div>


2. 下载并运行组网工具

    [点我下载**FRPC**](https://pan.i2cy.tech/s/aO3s8)
    - 下载后解压到任意目录，双击运行其中的`start_frpc.bat`，随后弹出的窗口不要关闭。若需结束组网关闭刚刚弹出的命令行窗口即可。


3. 使用Putty连接到核心板（确保组网工具FRPC正在运行）

    [点我下载**Putty**](https://pan.i2cy.tech/f/9OCw/putty.exe)
    - 打开`putty.exe`，在**Host Name**一栏填入
      ```
      127.0.0.1
      ```
    - 在Port一栏填入
      ```
      2300
      ```
    - 点击`Open`按钮
      <div align="center"><img width="244" src="https://pan.i2cy.tech/f/d4Fe/%7B0E14521B-B79D-4819-8FD5-0A546B49A568%7D.png"/></div>
    - 若是第一次连接，会弹出以下确认窗口，点击`accept`即可
      <div align="center"><img width="244" src="https://pan.i2cy.tech/f/jaiK/%7B59483F07-8FDD-486b-A786-8B3D92DABC50%7D.png"/></div>
    - 随后登陆，用户名为`pi`，密码也为`pi`（在**login as**出现之后输入`pi`，回车后继续输入`pi`然后回车）（另注tty登陆输入密码时不会显示，只管输入就行）
      <div align="center"><img width="244" src="https://pan.i2cy.tech/f/BNIa/%7B3484E5D6-835F-4bfc-AE8C-FF6345486686%7D.png"/></div>
    - 而后进入shell，可以执行测试命令
      <div align="center"><img width="244" src="https://pan.i2cy.tech/f/D5T2/%7BBB8B1BDC-7CC5-4745-BA10-BE675A92D1E0%7D.png"/></div>
    
    
## 执行测试

1. 运行SPI测试命令（运行即开始采集，按一次回车停止采集，若测试程序无响应请使用Ctrl+C组合键杀死进程）
   ```
   sudo python3 /home/pi/gtem/sources/spi_test.py
   ```
   

2. 停在此行说明正在等待FPGA的`spi_data_ready`标志
   <div align="center"><img width="244" src="https://pan.i2cy.tech/f/yAcR/%7B576CC8C9-5207-42fe-A29F-9E6DAAF86187%7D.png"/></div>


3. 一般收集3~4个`spi_data_ready`就可以按下回车键结束采集并校验数据


（注：若按下回车后长时间未出现校验结果，则可能是出现了未知阻塞，需要杀死进程重新测试，使用Ctrl+C组合键杀死当前进程，没反应就多按几下）


### 关于需要编辑代码
 - 请使用github VCS提交PR或直接联系作者编辑，更改同步到github后使用以下命令更新到设备
 - 代码更新命令
   ```
   cd /home/pi/gtem
   git fetch --all && git pull
   ```
 - 重新克隆命令
   ```
   clone -b test https://github.com/i2cy/GTEM_GUI /home/pi/gtem
   ```


### 附录：代码目录结构

 - ./sources/ （源码根目录）
   - assets/ （图标资源目录）
   - modules/ （代码模块目录）
     - **data.py** （数据流模块）
     - **data_multiproc.py** （协程数据流模块_已舍弃）
     - **debug.py** （debug标志）
     - **globals.py** （全局静态变量）
     - **graphic.py** （图表函数）
     - **gtem.py** （GTEM相关算法/二次场抽取）
     - **i2c.py** （I2C模块/FPGA/串转并）
     - **spi.py** （协程SPI模块/SPI读/SD卡写入）
     - **spi_dev_kernel.py** （内核级SPI模块_已舍弃）
     - **threads.py** （GUI前端线程）
     - **uart.py** （UART模块/GPS）
   - **main.py** （主程序入口/GUI前端代码文件）
   - **mainWindow.py** （GUI前端代码模块）
   - **mainWindow.ui** （转译前的QT前端文件）
   - **spi_test.py** （SPI数据完整性测试入口）