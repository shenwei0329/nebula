#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import time

def doCompScore(Labels, act_data, pref_data):
    """
    绘制综合指标（雷达图）
    :param Labels: 标题
    :param act_data: 实际值
    :param pref_data: 参考值
    :return: 图文件路径
    """
    angles = np.linspace(0, 2*np.pi, len(Labels), endpoint=False)
    data = np.concatenate((act_data, [act_data[0]]))
    max_data = np.concatenate((pref_data, [pref_data[0]]))
    angles = np.concatenate((angles, [angles[0]]))

    fig = plt.figure()
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, data, 'ro-', linewidth=1)
    ax.plot(angles, max_data, 'bo-.', linewidth=1)
    ax.set_thetagrids(angles * 180/np.pi, Labels )
    ax.fill(angles, data, facecolor='r', alpha=0.25)
    ax.fill(angles, max_data, facecolor='g', alpha=0.25)
    ax.set_rlim(0,1)

    ax.grid(True)
    _fn = 'pic/%s-compscore.png' % time.time()
    plt.savefig(_fn, dpi=75)
    return _fn

if __name__ == '__main__':

    doCompScore(['任务指标','出勤指标','计划指标'],(0.5833,0.7035,0.6023),(0.8,0.6544,0.8634))
