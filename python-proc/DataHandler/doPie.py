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

    labels = ['R&D', 'PJ', 'Other']
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
    return "在研产品投入：%d【人时】\n产品的项目定制化投入：%d【人时】\n其它事务投入：%d【人时】" % (data[0], data[1], data[2]), _fn
