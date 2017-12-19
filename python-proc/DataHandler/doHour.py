#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
"""
     线型（linestyle 简写为 ls）：
     实线： '-'
     虚线： '--'
     虚点线： '-.'
     点线： ':'
     点： '.' 
     点型（标记marker）：
     像素： ','
     圆形： 'o'
     上三角： '^'
     下三角： 'v'
     左三角： '<'
     右三角： '>'
     方形： 's'
     加号： '+' 
     叉形： 'x'
     棱形： 'D'
     细棱形： 'd'
     三脚架朝下： '1'（就是丫）
     三脚架朝上： '2'
     三脚架朝左： '3'
     三脚架朝右： '4'
     六角形： 'h'
     旋转六角形： 'H'
     五角形： 'p'
     垂直线： '|'
     水平线： '_'
     gnuplot 中的steps： 'steps' （只能用于kwarg中）
     标记大小（markersize 简写为 ms）： 
     markersize： 实数 
     标记边缘宽度（markeredgewidth 简写为 mew）：
     markeredgewidth：实数
     标记边缘颜色（markeredgecolor 简写为 mec）：
     markeredgecolor：颜色选项中的任意值
     标记表面颜色（markerfacecolor 简写为 mfc）：
     markerfacecolor：颜色选项中的任意值
     透明度（alpha）：
     alpha： [0,1]之间的浮点数
     线宽（linewidth）：
     linewidth： 实数
"""
import time
import matplotlib.pyplot as plt
import numpy as np
import numpy.random as rnd

def getTime(f):
     _s = ("%.2f") % f
     _s = _s.split('.')
     _h = int(_s[0])
     _m = int(_s[1])*60/100
     return ("%02d : %02d" % (_h, _m))

def doOprHour(data):

     plt.figure()
     x = range(len(data))
     _max = max(data)
     _min = min(data)
     _avg = sum(data)/len(data)

     plt.stem(x, data, '-.')
     plt.ylabel('Hour')
     plt.xlabel('Member')

     plt.xlim(-1, len(data)+1)
     plt.ylim(6, _max+1)
     plt.axhline(y=40, xmin=0, xmax=50, linestyle='-',linewidth=2, color='red', label='Normal')
     plt.axhline(y=_max, xmin=0, xmax=50, linestyle='--',linewidth=2, color='blue', label='Max:%d' % _max)
     plt.axhline(y=_avg, xmin=0, xmax=50, linestyle='-.',linewidth=2, color='green', label='Avg:%d' % _avg)
     plt.axhline(y=_min, xmin=0, xmax=50, linestyle=':',linewidth=2, color='red', label='Min:%d' % _min)
     plt.legend(loc=4)
     _fn = 'pic/%s-hour.png' % time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
     plt.savefig(_fn, dpi=75)
     #plt.show()
     return _fn

def doChkOnHourAtAM(data):
     """
     绘制考勤“上班”时间分布图
     :param data:
     :return:
     """
     plt.figure()
     x = range(len(data))
     _max = max(data)
     _min = min(data)
     _avg = sum(data) / len(data)
     plt.stem(x, data, '-.')

     plt.xlim(-1, len(data) + 1)
     plt.ylim(_min-1, _max + 1)

     plt.axhline(y=9, xmin=0, xmax=50, linestyle='-', linewidth=2, color='red', label='Normal_AM')
     plt.axhline(y=_max, xmin=0, xmax=50, linestyle='--', linewidth=2, color='blue', label='Max @%s' % getTime(_max))
     plt.axhline(y=_avg, xmin=0, xmax=50, linestyle='-.', linewidth=2, color='green', label='Avg @%s' % getTime(_avg))
     plt.axhline(y=_min, xmin=0, xmax=50, linestyle=':', linewidth=2, color='red', label='Min @%s' % getTime(_min))

     plt.legend()
     _fn = 'pic/%s-checkon_am.png' % time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
     plt.savefig(_fn, dpi=75)
     return _fn

def doChkOnHourAtPM(data):
     """
     绘制考勤“下班”时间分布图
     :param data:
     :return:
     """
     plt.figure()

     x = range(len(data))
     _max = max(data)
     _min = min(data)
     _avg = sum(data) / len(data)
     plt.stem(x, data, '-.')

     plt.xlim(-1, len(data) + 1)
     plt.ylim(_min-1, _max + 1)

     plt.axhline(y=17.5, xmin=0, xmax=50, linestyle='-', linewidth=2, color='red', label='Normal_PM')
     plt.axhline(y=_max, xmin=0, xmax=50, linestyle='--', linewidth=2, color='blue', label='Max @%s' % getTime(_max))
     plt.axhline(y=_avg, xmin=0, xmax=50, linestyle='-.', linewidth=2, color='green', label='Avg @%s' % getTime(_avg))
     plt.axhline(y=_min, xmin=0, xmax=50, linestyle=':', linewidth=2, color='red', label='Min @%s' % getTime(_min))

     """loc:
          1: upper right
          2: upper left
          3: lower left
          4: lower right
          5:right
          6:center left
          7:center right
          8:lower center
          9:upper center
          10:center
     """
     plt.legend(loc=4)
     _fn = 'pic/%s-checkon_pm.png' % time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
     plt.savefig(_fn, dpi=75)
     return _fn

def doChkOnHour(data1,data2):

     if data1 is None or data2 is None:
          return

     _pic1 = doChkOnHourAtAM(data1)
     _pic2 = doChkOnHourAtPM(data2)

     plt.figure()
     x = range(len(data1))
     _max1 = max(data1)
     _min1 = min(data1)
     _avg1 = sum(data1) / len(data1)
     plt.stem(x, data1, '-.')

     x = range(len(data2))
     _max2 = max(data2)
     _min2 = min(data2)
     _avg2 = sum(data2) / len(data2)
     plt.stem(x, data2, '-.')

     plt.ylabel('Hour')
     plt.xlabel('Record')

     plt.xlim(-1, len(data2) + 1)
     plt.ylim(6, max(_max1,_max2) + 1)

     plt.axhline(y=9, xmin=0, xmax=50, linestyle='-', linewidth=2, color='red', label='Normal_AM')
     plt.axhline(y=17.5, xmin=0, xmax=50, linestyle='-', linewidth=2, color='red', label='Normal_PM')

     _fn = 'pic/%s-checkon.png' % time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
     plt.savefig(_fn, dpi=75)
     # plt.show()
     return _pic1, _pic2, _fn
