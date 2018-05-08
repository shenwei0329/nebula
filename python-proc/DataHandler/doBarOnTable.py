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
    'font.size':8,
    })
    # Get some pastel shades for the colors
    colors = plt.cm.BuPu(np.linspace(0, 0.7, len(rows)))
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
    plt.subplots_adjust(left=0.2, bottom=0.3, top=0.96)

    plt.ylabel(u"工时",fontsize=fontsize)
    # plt.yticks(values * value_increment, ['%d' % val for val in values])
    plt.xticks([])
    plt.title(u'资源投入',fontsize=fontsize)

    _fn = 'pic/%s-barontable.png' % time.time()
    if not __test:
        plt.savefig(_fn, dpi=120)
    else:
        plt.show()
    return _fn

def getMemberbyGroup(cur):
    """
    获取 {组：组员} 字典
    :param cur: 数据源
    :return: 字典
    """

    _sql = 'select GRP_NAME from pd_group_t where GRP_STATE=1'
    _groups = doSQL(cur, _sql)

    _members = {}
    for _g in _groups:

        if _g[0] in sp_group:
            continue

        _member = []
        _sql = 'select MEMBER_NAME from pd_group_member_t where FLG=1'
        _res = doSQL(cur, _sql)
        for _m in _res:
            _member.append(_m[0])
        _members[_g[0]] = _member
    return _members

def getPdProject(cur):
    """
    获取 在研 产品项目信息
    :param cur: 数据源
    :return: 在研产品项目列表
    """

    _products = {}
    _sql = 'select PJ_XMBH,PJ_XMMC from project_t where PJ_XMXZ="产品研发"'
    _res = doSQL(cur, _sql)
    for _pd in _res:
        _products[_pd[0]] = _pd[1]
    return _products

def getProject(cur):
    """
    获取 工程交付 项目信息
    :param cur: 数据源
    :return: 工程交付项目列表
    """
    _projects = {}
    _sql = 'select PJ_XMBH,PJ_XMMC from project_t where PJ_XMXZ="工程交付"'
    _res = doSQL(cur, _sql)
    for _pd in _res:
        _projects[_pd[0]] = _pd[1]
    return _projects

def doWorkHourbyGroup(cur, begin_date=None, end_date=None):

    _member_group = getMemberbyGroup(cur)
    _products = getPdProject(cur)
    _projects = getProject(cur)

    """生成 各组 投入 在研产品 的工时"""
    _pd_col = ()
    _pd_row = []
    _pd_data = []
    for _g in _member_group:
        _pd_col += (_g,)
    for _pd in _products:
        _pd_row.append(_products[_pd])
        _data = []
        for _g in _pd_col:
            if (begin_date is None) or (end_date is None):
                _sql = 'select sum(TK_GZSJ+0.) from task_t where TK_XMBH="%s" and TK_SQR="%s"' % (_pd, _g)
            else:
                _sql = 'select sum(TK_GZSJ+0.) from task_t where ' \
                       'TK_XMBH="%s" and TK_SQR="%s" and created_at between "%s" and "%s"' % (
                            _pd, _g, begin_date, end_date)
            _cnt = doSQLcount(cur, _sql)
            _data.append(_cnt)
        _pd_data.append(_data)

    _pd_fn = doBarOnTable(_pd_row, _pd_col, _pd_data, figsize=(9,5), left=0.34, right=0.99,
                          bottom=0.16, top=0.94, fontsize=11)

    """生成 各组 投入 在项目与非项目 的工时"""
    _pd_row = [u'工程项目', u'非项目']
    _pd_data = []
    _data = []
    for _g in _pd_col:
        if (begin_date is None) or (end_date is None):
            _sql = 'select sum(TK_GZSJ+0.) from task_t where TK_XMBH<>"#" and ' \
                   'TK_XMBH not like "%%PRD-%%" and TK_SQR="%s"' % _g
        else:
            _sql = 'select sum(TK_GZSJ+0.) from task_t where ' \
                   'TK_XMBH<>"#" and TK_XMBH not like "%%PRD-%%" and ' \
                   'TK_SQR="%s" and created_at between "%s" and "%s"' % (
                        _g, begin_date, end_date)
        _cnt = doSQLcount(cur, _sql)
        _data.append(_cnt)
    _pd_data.append(_data)
    _data = []
    for _g in _pd_col:
        if (begin_date is None) or (end_date is None):
            _sql = 'select sum(TK_GZSJ+0.) from task_t where TK_XMBH="#" and TK_SQR="%s"' % _g
        else:
            _sql = 'select sum(TK_GZSJ+0.) from task_t where ' \
                   'TK_XMBH="#" and TK_SQR="%s" and created_at between "%s" and "%s"' % (
                        _g, begin_date, end_date)
        _cnt = doSQLcount(cur, _sql)
        _data.append(_cnt)
    _pd_data.append(_data)

    _pj_fn = doBarOnTable(_pd_row, _pd_col, _pd_data, figsize=(7,5), left=0.12, bottom=0.12, top=0.92, fontsize=11)

    return _pd_fn, _pj_fn

if __name__ == '__main__':

    __test = True
    data = [[ 66386, 174296,  75131, 577908,  32015],
            [ 58230, 381139,  78045,  99308, 160454],
            [ 89135,  80552, 152558, 497981, 603535],
            [ 78415,  81858, 150656, 193263,  69638],
            [139361, 331509, 343164, 781380,  52269]]

    columns = (u'设计组', u'系统组', u'云平台研发组', u'大数据研发组', u'测试组')
    rows = ['Hubble 1.8','Apollo 1.0','Fast 3.0','WhiteHole 1r1m1',u'混合云']

    values = np.arange(0, 2500, 500)
    value_increment = 1000

    index = np.arange(len(columns)) + 0.3

    doBarOnTable(rows,columns,data)
