#-*-i coding: utf-8 -*-
#
#
"""
==========
Table Demo
==========

Demo of table function to display a table within a plot.
"""
import numpy as np
import matplotlib.pyplot as plt
import time
from matplotlib import rcParams

__test = False

def doBarOnTable( rows, columns, datas ):
    """
    组合 柱状图 和 表格 显示图示
    :param rows: 列 标签（如 产品、任务）
    :param columns: 行 标签（如 资源组）
    :param datas: 二维数据组
    :return:
    """
    index = np.arange(len(columns)) + 0.3
    plt.figure()
    rcParams.update({
    'font.family':'sans-serif',
    'font.sans-serif':[u'SimHei'],
    'axes.unicode_minus':False,
    })
    # Get some pastel shades for the colors
    colors = plt.cm.BuPu(np.linspace(0, 0.5, len(rows)))
    n_rows = len(datas)
    bar_width = 0.4
    # Initialize the vertical-offset for the stacked bar chart.
    y_offset = np.zeros(len(columns))
    # Plot bars and create text labels for the table
    cell_text = []
    _N = n_rows-1
    for row in range(n_rows):
        plt.bar(index, datas[_N-row], bar_width, bottom=y_offset, color=colors[row])
        y_offset = y_offset + datas[_N-row]
        cell_text.append(['%d' % x for x in datas[_N-row]])
    # Reverse colors and text labels to display the last value at the top.
    colors = colors[::-1]
    cell_text.reverse()

    print cell_text

    # Add a table at the bottom of the axes
    plt.table(cellText=cell_text,rowLabels=rows,rowColours=colors,colLabels=columns,loc='bottom')

    # Adjust layout to make room for the table:
    plt.subplots_adjust(left=0.2, bottom=0.4)

    plt.ylabel(u"工时")
    #plt.yticks(values * value_increment, ['%d' % val for val in values])
    plt.xticks([])
    plt.title(u'资源投入')

    _fn = 'pic/%s-barontable.png' % time.time()
    if not __test:
        plt.savefig(_fn, dpi=75)
    else:
        plt.show()
    return _fn

if __name__ == '__main__':

    data = [[ 66386, 174296,  75131, 577908,  32015],
            [ 58230, 381139,  78045,  99308, 160454],
            [ 89135,  80552, 152558, 497981, 603535],
            [ 78415,  81858, 150656, 193263,  69638],
            [139361, 331509, 343164, 781380,  52269]]

    columns = (u'设计组', u'系统组', u'云平台研发组', u'大数据研发组', u'测试组')
    rows = ['Hubble 1.8','Apollo 1.0','Fast 3.0','WhiteHole 1r1m1','Mir 1.5']

    values = np.arange(0, 2500, 500)
    value_increment = 1000

    index = np.arange(len(columns)) + 0.3

    doBarOnTable(rows,columns,data)
