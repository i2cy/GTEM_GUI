%%%%%%%%%%%%%%%%%%%%瞬变电磁数据处理%%%%%%%%%%%%%%%%%
%data1放测试数据
close all;
clear all;
clc;
%原始文件存放在'C:\Users\Lee\Desktop\dataTEM'
maindir = ['E:\BaiduSyncdisk\DateBasedProjects\2022\' ...
    '9.3 地面接收机软件\sample\GTEM_tests\dataTEM1'];
userpath(maindir);%编译文件存放地方
%接收机设置放大倍数
GAIN = 0.25;
%采样率
SPS = 25000;
%采样位数
N = 24;
%发射频率
emit_freq = 25;%5
%二次场峰值
peak_point = 127;%100k为504，25k为127,800k为4022
%原始数据去除激变值
read_raw_data_filter = 1;
%raw_data读取的原始信号,file_num为读取的文件个数,文件存放位 文件批处理data1
subdir = dir( maindir );
file_num = (length( subdir )-2)*60;%存储文件个数
data = [];
control = [];

% 循环读取data1下的文件存储在data中
for jn = 1:1:length( subdir )
    if(subdir( jn ).isdir)  % 如果是目录则跳过,isdir判断是否为文件夹
        continue;
    end
    %获取文件途径，存储在datpath变量中
    datpath = fullfile( maindir, subdir(jn ).name);
    %依次一个文件一个文件读取了数据
    fid=fopen(datpath,'r');
    [data_read,num]=fread(fid,'uchar');
    %将无符号数转换为有符号数
    result1=uint32(data_read);
    %将24bit数据转换成一个数据
    i=0;%间隔4
    for j=1:4:num
        i=i+1;
        %result2(i)=result1(j);  %多少组数据 01 02 03 00小端法排列
        result2(i)=result1(j)+ (result1(j+1)+ result1(j+2)*256)*256;  %多少组数据
        result3(i)=result1(j+3);
    end
    %将数据转换成有效数据
    for i=1:1:length(result2)
        if(result2(i)<2^(N-1))
            result(i)=int32(result2(i));
        else
            result(i)=-1*int32(2^N-result2(i));
        end
    end
    %转换成uv单位，半边参考电压4.096v
    data_analog_ban0=(double(result) /(2^(N-1)-1))*4096*1/GAIN;%参考电压4.096,LTC2380增益压缩开启
    %将所有的数据存储在data中，data中存放全部时间内的数据
    data= [data,data_analog_ban0];
    control=[control,mod(result3,256)];
end
%D00=3.14*0.25*0.25*384*14; 转换为nT/s sig_noise=data*10^6/D00;%mv*10^6=nV
sig_noise=data*10^3;%uV%注意单位
% %
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% % %一条测线中，每次叠加的秒数 % %每次叠加的时间间隔
%抽道数
choudao=24;
len=60;      %叠加的时间间隔1s
[sig_noise_sum,t,c]=gate_trace_secondary_field_extract(sig_noise,SPS,emit_freq,peak_point,len,read_raw_data_filter);
figure(1)
x=1:(SPS/emit_freq/4*0.9);
loglog(x/(SPS/1000),sig_noise_sum,'b');grid on;% 时间轴单位ms
hold on;
xlabel('ms');
ylabel('nT/s');