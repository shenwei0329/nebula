#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#

import time
import matplotlib.pyplot as plt
import numpy as np
import numpy.random as rnd

def doProjectPie(data):
    """

    :param data: 【 产品研发时间， 项目时间， 其它 】
    :return:
    """

    labels = ['产品项目', '工程项目', '非项目类']
    #plt.figure(figsize=(3, 4))
    plt.figure()
    colors = ['green','yellowgreen','lightskyblue']
    explode = (0.05, 0, 0.03)

    plt.pie(data, labels=labels, colors=colors, explode=explode,shadow=True, autopct='%3.1f%%', pctdistance=0.6)
    plt.axis('equal')
    plt.legend()
    _fn = 'pic/%s-project.png' % time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
    plt.savefig(_fn, dpi=75)
    #plt.show()
    return _fn
