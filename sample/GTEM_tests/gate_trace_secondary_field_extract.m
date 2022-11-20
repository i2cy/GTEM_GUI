% 先提取每个周期内的二次场，反向叠加后，再进行抽道，然后再叠加
%data为待处理数据，D0放大倍数，SPS采样率，emit_freq发射频率
%peak_point峰值点，len为本次叠加的时间长度,read_raw_data_filter读出数据做均滑滤波
function [data_ban09,tt,data_ban_gate_1]=gate_trace_secondary_field_extract(data,SPS,emit_freq,peak_point,len,read_raw_data_filter)
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %存储峰值
%     data=raw_data1;
t_peak_point=peak_point;
 %计算叠加次数
add_time=emit_freq*len;
 %叠加data内多个周期数据
data_ban00=zeros(add_time,SPS/emit_freq/4*0.9);

%数据预处理，缩小差值
if(read_raw_data_filter==1)
     for k=1:1:add_time
             for x=1:1:SPS/emit_freq/4*0.9-1
                 if(data(peak_point)>0)
                     if(data(x+peak_point)>data(x+peak_point-1))
                         d=data(x+peak_point)-data(x+peak_point-1);
                         data(x+peak_point)=data(x+peak_point)-d/2;
                         data(x+peak_point-1)=data(x+peak_point-1)+d/2;
                     end
                 else 
                     if(data(x+peak_point)< data(x+peak_point-1))
                         d=data(x+peak_point-1)-data(x+peak_point);
                         data(x+peak_point)=data(x+peak_point)+d/2;
                         data(x+peak_point-1)=data(x+peak_point-1)-d/2;
                     end
                 end
             end
                peak_point=peak_point+SPS/emit_freq/2;
     end 
end
 %叠加一个周期后取平均 
 peak_point=t_peak_point;
if(data(peak_point)>0)
   flag=1;
else 
   flag=0;
end
 for k=1:1:(add_time)
         for x=1:1:SPS/emit_freq/4*0.9
             if(flag==1)
             data_ban00(k,x)=(+data(x+peak_point-1)-data(x+peak_point-1+SPS/emit_freq/2))/2;
             else 
             data_ban00(k,x)=(-data(x+peak_point-1)+data(x+peak_point-1+SPS/emit_freq/2))/2;
             end
         end
            peak_point=peak_point+SPS/emit_freq;
 end 
 %直接输出
 if 1
     data_ban09=sum(data_ban00,1)/add_time;
     data_ban_gate_1=data_ban09;
     if (min(data_ban09)<=0)
         %data_ban09=data_ban09- min(data_ban09)+0.0001;
     end
     tt=1;
 end
 %先叠加在滤波
 if 0
  for k=1:1:(add_time)
      %去除负值，拟合指数的衰减
%   n_min=find(data_ban00(k,:)==min(data_ban00(k,:)));
%           if n_min<288
%              data_ban00(k,:)=data_ban00(k,:)- min(data_ban00(k,:))+0.1;
%              expfit_x=n_min:288;
%              data_new = 0.1*exp(-0.00000001*expfit_x);
%              data_ban00(k,expfit_x)=data_new;
%           else 
%               if min(data_ban00(k,:))<0
%               data_ban00(k,:)=data_ban00(k,:)- min(data_ban00(k,:))+0.1;
%               end
%           end
           if min(data_ban00(k,:))<0
           data_ban00(k,:)=data_ban00(k,:)- min(data_ban00(k,:))+0.1;
           end
  end
 %选择性叠加，通过求取一个标准差内的点，去除异常点
  max_mean=mean(data_ban00);
  max_std=std(data_ban00);
  %一个标准差,得到要去除点位
  gata_interval_1=find(data_ban00(:,1)>(max_mean(1)+max_std(1)));
  gata_interval_2=find(data_ban00(:,1)<(max_mean(1)-max_std(1)));
%汉宁窗滤除按照每一道进行滤波
 data_ban00_3=data_ban00;
  %构建窗函数
%   win=hanning(add_time);
%   %按道进行滤波
%   for k=1:24
%   data_ban_gate_3(:,k)=data_ban_gate(:,k).*win;
%   end
  %异常点为nan,b不参加运算
  data_ban00_2=data_ban00_3;
  data_ban00_2(gata_interval_1,:)=nan;
  data_ban00_2(gata_interval_2,:)=nan;
  %去除指数值,防止几何平均溢出
  coef=abs(max(data_ban00_2));
  coef_max=repmat(coef,add_time,1);
  data_ban00_1=data_ban00_2./coef_max;
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  %nan值切换为1
  data_ban00_1(gata_interval_1,:)=1;
  data_ban00_1(gata_interval_2,:)=1;
  %几何平均，加修正
  %含窗函数的修正
%     data_ban09=abs(prod(data_ban_gate_1).^(1/(add_time-length(gata_interval_1)-length(gata_interval_2))))/(prod(win)^(1/length(win))).*coef;
  %不含窗函数的修正
  data_ban09=abs(prod(data_ban00_1).^(1/(add_time-length(gata_interval_1)-length(gata_interval_2)))).*coef;
  tt=1;
  data_ban_gate_1=data_ban00_1;
 end
 
 if 0%先抽道，再叠加
    %选择性叠加，通过求取一个标准差内的点，去除异常点
   for k=1:1:(add_time) 
       data_ban_gate(k,:)=extract(data_ban00,emit_freq,SPS);
%        n_min=find(data_ban_gate(k,:)==min(data_ban_gate(k,:)));
%           if n_min<24
%              data_ban_gate(k,:)=data_ban_gate(k,:)- min(data_ban_gate(k,:))+0.1;
%              expfit_x=n_min:24;
%              data_new = 0.1*exp(-0.00000001*expfit_x);
%              data_ban_gate(k,expfit_x)=data_new;
%           else 
%               if min(data_ban_gate(k,:))<0
%               data_ban_gate(k,:)=data_ban_gate(k,:)- min(data_ban_gate(k,:))+0.1;
%               end
%           end
%            if min(data_ban_gate(k,:))<0
%            data_ban_gate(k,:)=data_ban_gate(k,:)- min(data_ban_gate(k,:))+0.1;
%            end
   end
 
  max_mean=mean(data_ban_gate);
  max_std=std(data_ban_gate);
  %一个标准差,得到要去除点位
  gata_interval_1=find(data_ban_gate(:,1)>(max_mean(1)+max_std(1)));
  gata_interval_2=find(data_ban_gate(:,1)<(max_mean(1)-max_std(1)));
%汉宁窗滤除按照每一道进行滤波
  data_ban_gate_3=data_ban_gate;
  %构建窗函数
%   win=hanning(add_time);
%   %按道进行滤波
%   for k=1:24
%   data_ban_gate_3(:,k)=data_ban_gate(:,k).*win;
%   end
  %异常点为nan,b不参加运算
  data_ban_gate_2=data_ban_gate_3;
  data_ban_gate_2(gata_interval_1,:)=nan;
  data_ban_gate_2(gata_interval_2,:)=nan;
  %去除指数值,防止几何平均溢出
  coef=abs(max(data_ban_gate_2));
  coef_max=repmat(coef,add_time,1);
  data_ban_gate_1=data_ban_gate_2./coef_max;
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  %nan值切换为1
  data_ban_gate_1(gata_interval_1,:)=1;
  data_ban_gate_1(gata_interval_2,:)=1;
  %几何平均，加修正
  %含窗函数的修正
%     data_ban09=abs(prod(data_ban_gate_1).^(1/(add_time-length(gata_interval_1)-length(gata_interval_2))))/(prod(win)^(1/length(win))).*coef;
  %不含窗函数的修正
  data_ban09=abs(prod(data_ban_gate_1).^(1/(add_time-length(gata_interval_1)-length(gata_interval_2)))).*coef; 
 end
