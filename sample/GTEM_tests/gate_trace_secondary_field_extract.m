% ����ȡÿ�������ڵĶ��γ���������Ӻ��ٽ��г����Ȼ���ٵ���
%dataΪ���������ݣ�D0�Ŵ�����SPS�����ʣ�emit_freq����Ƶ��
%peak_point��ֵ�㣬lenΪ���ε��ӵ�ʱ�䳤��,read_raw_data_filter���������������˲�
function [data_ban09,tt,data_ban_gate_1]=gate_trace_secondary_field_extract(data,SPS,emit_freq,peak_point,len,read_raw_data_filter)
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %�洢��ֵ
%     data=raw_data1;
t_peak_point=peak_point;
 %������Ӵ���
add_time=emit_freq*len;
 %����data�ڶ����������
data_ban00=zeros(add_time,SPS/emit_freq/4*0.9);

%����Ԥ������С��ֵ
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
 %����һ�����ں�ȡƽ�� 
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
 %ֱ�����
 if 1
     data_ban09=sum(data_ban00,1)/add_time;
     data_ban_gate_1=data_ban09;
     if (min(data_ban09)<=0)
         %data_ban09=data_ban09- min(data_ban09)+0.0001;
     end
     tt=1;
 end
 %�ȵ������˲�
 if 0
  for k=1:1:(add_time)
      %ȥ����ֵ�����ָ����˥��
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
 %ѡ���Ե��ӣ�ͨ����ȡһ����׼���ڵĵ㣬ȥ���쳣��
  max_mean=mean(data_ban00);
  max_std=std(data_ban00);
  %һ����׼��,�õ�Ҫȥ����λ
  gata_interval_1=find(data_ban00(:,1)>(max_mean(1)+max_std(1)));
  gata_interval_2=find(data_ban00(:,1)<(max_mean(1)-max_std(1)));
%�������˳�����ÿһ�������˲�
 data_ban00_3=data_ban00;
  %����������
%   win=hanning(add_time);
%   %���������˲�
%   for k=1:24
%   data_ban_gate_3(:,k)=data_ban_gate(:,k).*win;
%   end
  %�쳣��Ϊnan,b���μ�����
  data_ban00_2=data_ban00_3;
  data_ban00_2(gata_interval_1,:)=nan;
  data_ban00_2(gata_interval_2,:)=nan;
  %ȥ��ָ��ֵ,��ֹ����ƽ�����
  coef=abs(max(data_ban00_2));
  coef_max=repmat(coef,add_time,1);
  data_ban00_1=data_ban00_2./coef_max;
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  %nanֵ�л�Ϊ1
  data_ban00_1(gata_interval_1,:)=1;
  data_ban00_1(gata_interval_2,:)=1;
  %����ƽ����������
  %��������������
%     data_ban09=abs(prod(data_ban_gate_1).^(1/(add_time-length(gata_interval_1)-length(gata_interval_2))))/(prod(win)^(1/length(win))).*coef;
  %����������������
  data_ban09=abs(prod(data_ban00_1).^(1/(add_time-length(gata_interval_1)-length(gata_interval_2)))).*coef;
  tt=1;
  data_ban_gate_1=data_ban00_1;
 end
 
 if 0%�ȳ�����ٵ���
    %ѡ���Ե��ӣ�ͨ����ȡһ����׼���ڵĵ㣬ȥ���쳣��
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
  %һ����׼��,�õ�Ҫȥ����λ
  gata_interval_1=find(data_ban_gate(:,1)>(max_mean(1)+max_std(1)));
  gata_interval_2=find(data_ban_gate(:,1)<(max_mean(1)-max_std(1)));
%�������˳�����ÿһ�������˲�
  data_ban_gate_3=data_ban_gate;
  %����������
%   win=hanning(add_time);
%   %���������˲�
%   for k=1:24
%   data_ban_gate_3(:,k)=data_ban_gate(:,k).*win;
%   end
  %�쳣��Ϊnan,b���μ�����
  data_ban_gate_2=data_ban_gate_3;
  data_ban_gate_2(gata_interval_1,:)=nan;
  data_ban_gate_2(gata_interval_2,:)=nan;
  %ȥ��ָ��ֵ,��ֹ����ƽ�����
  coef=abs(max(data_ban_gate_2));
  coef_max=repmat(coef,add_time,1);
  data_ban_gate_1=data_ban_gate_2./coef_max;
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  %nanֵ�л�Ϊ1
  data_ban_gate_1(gata_interval_1,:)=1;
  data_ban_gate_1(gata_interval_2,:)=1;
  %����ƽ����������
  %��������������
%     data_ban09=abs(prod(data_ban_gate_1).^(1/(add_time-length(gata_interval_1)-length(gata_interval_2))))/(prod(win)^(1/length(win))).*coef;
  %����������������
  data_ban09=abs(prod(data_ban_gate_1).^(1/(add_time-length(gata_interval_1)-length(gata_interval_2)))).*coef; 
 end
