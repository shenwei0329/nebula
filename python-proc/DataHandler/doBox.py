#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#

import numpy as np
import matplotlib.pyplot as plt
from pylab import plot, show, savefig, xlim, figure, \
                hold, ylim, legend, boxplot, setp, axes
import time,random

def doBox(label,datas):
    fig = figure()
    ax = axes()
    hold(True)

    boxplot(datas, positions=range(1,len(label)+1), widths=0.6)
    # set axes limits and labels
    xlim(0, len(label)+1)
    ylim(-0.2, 1.2)
    ax.set_xticklabels(label)
    _fn = 'pic/%s-box.png' % time.time()
    savefig(_fn, dpi=75)
    #show()
    return _fn

def doBar(title, y_label, x_label, datas):

    plt.figure()
    ind = np.arange(len(x_label))  # the x locations for the groups
    plt.bar(ind, datas, 0.35, color='#afafaf')
    plt.ylabel(y_label)
    plt.title(title)
    plt.xticks(ind, x_label)
    _fn = 'pic/%s-bar.png' % time.time()
    savefig(_fn, dpi=75)
    #show()
    return _fn

def doBarH(title, y_label, x_label, datas):

    plt.figure()
    ind = np.arange(len(x_label))+1  # the x locations for the groups
    plt.barh(ind, datas, 0.35, 0.5, align='edge', color='#afafaf')
    plt.xlabel(y_label)
    plt.title(title)
    plt.yticks(ind, x_label)
    _fn = 'pic/%s-bar.png' % time.time()
    savefig(_fn, dpi=75)
    #show()
    return _fn

if __name__ == '__main__':

    _v = [714, 667, 372, 347, 61, 60, 54, 52, 47, 30, 14, 4]
    _l = []
    for i in range(12):
        _l.append('%d' % (i+1))

    doBarH('test','val',_l,_v)
