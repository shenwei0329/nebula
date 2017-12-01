#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#

import numpy as np
import matplotlib.pyplot as plt
from pylab import plot, show, savefig, xlim, figure, \
                hold, ylim, legend, boxplot, setp, axes
import time,random

__test = False

def doBox(label,datas,y_line=None,y_limit=None,y_label=None,x_label=None):
    fig = figure()
    ax = axes()
    hold(True)

    for _data in datas:
        boxplot(_data, positions=range(1,len(label)+1), widths=0.6)
    # set axes limits and labels
    xlim(0, len(label)+1)
    if y_limit is not None:
        ylim(y_limit[0], y_limit[1])
    if y_line is not None:
        for _l in y_line:
            plt.axhline(y=_l,linestyle='-.', linewidth=1, color='red')
    ax.set_xticklabels(label)
    if y_label is not None:
        plt.ylabel(y_label)
    if x_label is not None:
        plt.xlabel(x_label)

    if not __test:
        _fn = 'pic/%s-box.png' % time.time()
        savefig(_fn, dpi=75)
    else:
        show()
    return _fn

def doBar(title, y_label, x_label, datas, label=None, y_limit=None):

    plt.figure()
    ind = np.arange(len(x_label))  # the x locations for the groups
    _i = 0
    for _d in datas:
        if label is not None:
            plt.bar(ind, _d[0], 0.35, color=_d[1], label=label[_i])
        else:
            plt.bar(ind, _d[0], 0.35, color=_d[1])
        _i += 1
    if y_limit is not None:
        ylim(0,y_limit)
    plt.ylabel(y_label)
    plt.title(title)
    plt.xticks(ind, x_label)
    if label is not None:
        plt.legend()
    if not __test:
        _fn = 'pic/%s-bar.png' % time.time()
        savefig(_fn, dpi=75)
    else:
        show()
    return _fn

def doBarH(title, y_label, x_label, datas):

    plt.figure()
    ind = np.arange(len(x_label))+1  # the x locations for the groups
    plt.barh(ind, datas, 0.35, 0.5, align='edge', color='#afafaf')
    plt.xlabel(y_label)
    plt.title(title)
    plt.yticks(ind, x_label)
    if not __test:
        _fn = 'pic/%s-bar.png' % time.time()
        savefig(_fn, dpi=75)
    else:
        show()
    return _fn

if __name__ == '__main__':

    global __test

    __test = True

    label = ['Mo','Tu','We','Th','Fr','Sa','Su','Avg']
    datas = []
    for _i in range(2): # Am & Pm
        _data = []
        for _j in range(len(label)):
            _d = ()
            for _k in range(10):
                if _i == 0:
                    _v = random.uniform(6, 12)
                else:
                    _v = random.uniform(12, 24)
                _d += (_v,)
            _data.append(_d)
        datas.append(_data)
    doBox(label,datas,y_limit=(5.,24.),y_line=(9.,17.5,))
    """
    _v = [714, 667, 372, 347, 61, 60, 54, 52, 47, 30, 14, 4]
    _l = []
    for i in range(12):
        _l.append('%d' % (i+1))

    doBarH('test','val',_l,_v)
    """