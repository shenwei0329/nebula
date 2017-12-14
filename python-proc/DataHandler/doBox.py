#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#

import numpy as np
import matplotlib.pyplot as plt
from pylab import plot, show, savefig, xlim, figure, \
                hold, ylim, legend, boxplot, setp, axes
import time,random

"""
设置图例显示的位置
label_pos:
===========

'best'         : 0, (only implemented for axes legends)(自适应方式)
'upper right'  : 1,
'upper left'   : 2,
'lower left'   : 3,
'lower right'  : 4,
'right'        : 5,
'center left'  : 6,
'center right' : 7,
'lower center' : 8,
'upper center' : 9,
'center'       : 10,
"""
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
            plt.axhline(y=_l,linestyle='-', linewidth=1, color='red')
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
    _b = np.zeros(len(x_label))     # the x locations for the groups
    _i = 0
    for _d in datas:
        if label is not None:
            plt.bar(ind, _d[0], 0.35, color=_d[1], bottom=_b, label=label[_i])
        else:
            plt.bar(ind, _d[0], 0.35, bottom=_b, color=_d[1])
        _b = _b + _d[0]
        print _b
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

def doDotBase(title, y_label, x_label, datas, limit=None, label_pos=None, lines=None, ylines=None, dots=None):

    plt.figure()
    for _data in datas:
        _color = _data[1]
        _dot = _data[2]
        _label = _data[3]
        plt.plot(range(len(_data[0])),_data[0],_dot,label=_label, color=_color)

    if limit is not None:
        ylim(limit[0],limit[1])

    if dots is not None:
        for _dot in dots:
            plt.scatter(_dot[0], _dot[1], marker=_dot[2], color=_dot[3], label=_dot[4])

    if lines is not None:
        for _line in lines:
            plt.axvline(x=_line[0], linestyle=_line[1], linewidth=2, color=_line[2], label=_line[3])

    if ylines is not None:
        for _line in ylines:
            plt.axhline(y=_line[0], linestyle=_line[1], linewidth=1, color=_line[2], label=_line[3])

    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.title(title)
    if label_pos is None:
        plt.legend()
    else:
        plt.legend(loc=label_pos)

    _fn = 'pic/%s-bar.png' % time.time()
    if not __test:
        plt.savefig(_fn, dpi=75)
    else:
        plt.show()
    return _fn

def doStem(title, y_label, x_label, datas, limit=None, label_pos=None, lines=None, ylines=None, dots=None):

    plt.figure()
    for _data in datas:
        _color = _data[1]
        _dot = _data[2]
        _label = _data[3]
        markerline, stemlines, baseline = plt.stem(_data[0][0],_data[0][1],_dot, label=_label)
        plt.setp(markerline, 'markerfacecolor', _color)
        plt.setp(stemlines, 'color', _color, 'linewidth', 1)
        plt.setp(baseline, 'color', 'k', 'linewidth', 1)

    if limit is not None:
        ylim(limit[0],limit[1])

    if dots is not None:
        for _dot in dots:
            plt.scatter(_dot[0], _dot[1], marker=_dot[2], color=_dot[3], label=_dot[4])

    if lines is not None:
        for _line in lines:
            plt.axvline(x=_line[0], linestyle=_line[1], linewidth=1, color=_line[2], label=_line[3])

    if ylines is not None:
        for _line in ylines:
            plt.axhline(y=_line[0], linestyle=_line[1], linewidth=1, color=_line[2], label=_line[3])

    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.title(title)
    if label_pos is None:
        plt.legend()
    else:
        plt.legend(loc=label_pos)

    _fn = 'pic/%s-stem.png' % time.time()
    if not __test:
        plt.savefig(_fn, dpi=75)
    else:
        plt.show()
    return _fn

def doLine(title, y_label, x_label, datas, limit=None, label_pos=None, lines=None, ylines=None, dots=None):

    plt.figure()
    _max = 0
    for _data in datas:
        _color = _data[1]
        _dot = _data[2]
        _label = _data[3]
        for _i in _data[0][0]:
            if _max < _data[0][1][_i][1]+1:
                _max = _data[0][1][_i][1]+1
            plt.plot([_i, _i], [_data[0][1][_i][0], _data[0][1][_i][1]], _dot, linewidth=3, color=_color)
        plt.plot([_i, _i], [_data[0][1][_i][0], _data[0][1][_i][1]], _dot, linewidth=3, color=_color, label=_label)

    ylim(-1, _max+float(_max)*0.1)

    if dots is not None:
        for _dot in dots:
            plt.scatter(_dot[0], _dot[1], marker=_dot[2], color=_dot[3], label=_dot[4])

    if lines is not None:
        for _line in lines:
            plt.axvline(x=_line[0], linestyle=_line[1], linewidth=1, color=_line[2], label=_line[3])

    if ylines is not None:
        for _line in ylines:
            plt.axhline(y=_line[0], linestyle=_line[1], linewidth=1, color=_line[2], label=_line[3])

    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.title(title)
    if label_pos is None:
        plt.legend()
    else:
        plt.legend(loc=label_pos)

    _fn = 'pic/%s-line.png' % time.time()
    if not __test:
        plt.savefig(_fn, dpi=75)
    else:
        plt.show()
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