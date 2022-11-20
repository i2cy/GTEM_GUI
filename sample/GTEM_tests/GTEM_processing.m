%%%%%%%%%%%%%%%%%%%%˲�������ݴ���%%%%%%%%%%%%%%%%%
%data1�Ų�������
close all;
clear all;
clc;
%ԭʼ�ļ������'C:\Users\Lee\Desktop\dataTEM'
maindir = ['E:\BaiduSyncdisk\DateBasedProjects\2022\' ...
    '9.3 ������ջ����\sample\GTEM_tests\dataTEM1'];
userpath(maindir);%�����ļ���ŵط�
%���ջ����÷Ŵ���
GAIN = 0.25;
%������
SPS = 25000;
%����λ��
N = 24;
%����Ƶ��
emit_freq = 25;%5
%���γ���ֵ
peak_point = 127;%100kΪ504��25kΪ127,800kΪ4022
%ԭʼ����ȥ������ֵ
read_raw_data_filter = 1;
%raw_data��ȡ��ԭʼ�ź�,file_numΪ��ȡ���ļ�����,�ļ����λ �ļ�������data1
subdir = dir( maindir );
file_num = (length( subdir )-2)*60;%�洢�ļ�����
data = [];
control = [];

% ѭ����ȡdata1�µ��ļ��洢��data��
for jn = 1:1:length( subdir )
    if(subdir( jn ).isdir)  % �����Ŀ¼������,isdir�ж��Ƿ�Ϊ�ļ���
        continue;
    end
    %��ȡ�ļ�;�����洢��datpath������
    datpath = fullfile( maindir, subdir(jn ).name);
    %����һ���ļ�һ���ļ���ȡ������
    fid=fopen(datpath,'r');
    [data_read,num]=fread(fid,'uchar');
    %���޷�����ת��Ϊ�з�����
    result1=uint32(data_read);
    %��24bit����ת����һ������
    i=0;%���4
    for j=1:4:num
        i=i+1;
        %result2(i)=result1(j);  %���������� 01 02 03 00С�˷�����
        result2(i)=result1(j)+ (result1(j+1)+ result1(j+2)*256)*256;  %����������
        result3(i)=result1(j+3);
    end
    %������ת������Ч����
    for i=1:1:length(result2)
        if(result2(i)<2^(N-1))
            result(i)=int32(result2(i));
        else
            result(i)=-1*int32(2^N-result2(i));
        end
    end
    %ת����uv��λ����߲ο���ѹ4.096v
    data_analog_ban0=(double(result) /(2^(N-1)-1))*4096*1/GAIN;%�ο���ѹ4.096,LTC2380����ѹ������
    %�����е����ݴ洢��data�У�data�д��ȫ��ʱ���ڵ�����
    data= [data,data_analog_ban0];
    control=[control,mod(result3,256)];
end
%D00=3.14*0.25*0.25*384*14; ת��ΪnT/s sig_noise=data*10^6/D00;%mv*10^6=nV
sig_noise=data*10^3;%uV%ע�ⵥλ
% %
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% % %һ�������У�ÿ�ε��ӵ����� % %ÿ�ε��ӵ�ʱ����
%�����
choudao=24;
len=60;      %���ӵ�ʱ����1s
[sig_noise_sum,t,c]=gate_trace_secondary_field_extract(sig_noise,SPS,emit_freq,peak_point,len,read_raw_data_filter);
figure(1)
x=1:(SPS/emit_freq/4*0.9);
loglog(x/(SPS/1000),sig_noise_sum,'b');grid on;% ʱ���ᵥλms
hold on;
xlabel('ms');
ylabel('nT/s');