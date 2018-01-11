#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.dates import AutoDateLocator, DateFormatter
from pylab import figure, axes
import MySQLdb, sys, time
import matplotlib.pyplot as plt

"""
temp = zip(x, y2)
# 在柱状图上显示具体数值, ha水平对齐, va垂直对齐
for x, y in zip(x, y1):
    plt.text(x + 0.05, y + 0.1, '%.2f' % y, ha = 'center', va = 'bottom')

for x, y in temp:
    plt.text(x + 0.05, -y - 0.1, '%.2f' % y, ha = 'center', va = 'bottom')

# 设置坐标轴范围
plt.xlim(-1, n)
plt.ylim(-1.5, 1.5)
# 去除坐标轴
plt.xticks(())
plt.yticks(())
plt.show()
"""

_test_mod = False

reload(sys)
sys.setdefaultencoding('utf-8')

def doSQL(cur,_sql):

    cur.execute(_sql)
    return cur.fetchall()

def doJinkinsCoverage(cur):
    """
    绘制 Jenkins 代码单元测试的覆盖分布图
    :param cur: 数据源
    :return: 图文件路径
    """
    """准备数据"""
    _filename = []
    _line_rate = ()
    _branch_rate = ()
    __complexity = ()
    _sql = 'select filename,line_rate,branch_rate,complexity from jenkins_coverage_t ' \
           'where filename<>"#" and filename like "%Controller.java%"'
    _res = doSQL(cur, _sql)

    _max = 0.
    for _r in _res:
        _fn = _r[0][_r[0].rfind('/')+1:]
        _filename.append(_fn)
        _line_rate += (float(_r[1]),)
        _branch_rate += (-float(_r[2]),)
        __complexity += (float(_r[3]),)
        if float(_r[3]) > _max:
            _max = float(_r[3])

    _complexity = ()
    for _c in __complexity:
        _complexity += (_c*1.2 / _max, )

    """作图"""
    rcParams.update({
    'font.family':'sans-serif',
    'font.sans-serif':[u'SimHei'],
    'axes.unicode_minus':False,
    'font.size':8,
    })

    fig = figure(figsize=[10, 8])

    ax = fig.add_subplot(111)
    _x = range(1, len(_line_rate)+1)
    ax.bar(_x, _line_rate, facecolor='blue', edgecolor='white', align='center', label=u'行覆盖率')
    ax.bar(_x, _branch_rate, facecolor='green', edgecolor='white', align='center', label=u'分支覆盖率')
    ax.bar(_x, _complexity, 0.2, facecolor='red', edgecolor='red', label=u'复杂度')
    ax.set_xticks(range(1,len(_filename)+1))
    ax.set_xticklabels(_filename,rotation='vertical', fontsize=11)
    ax.legend()

    plt.xlim(0, len(_line_rate)+1)
    plt.ylim(-1.3, 1.3)

    ax.grid(True)

    plt.title(u'单元测试覆盖率', fontsize=12)
    plt.subplots_adjust(left=0.06, right=0.98, bottom=0.41, top=0.9)

    _fn = 'pic/%s-coverage.png' % time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    if not _test_mod:
        plt.savefig(_fn, dpi=120)
    else:
        plt.show()
    return _fn

if __name__ == '__main__':

    _test_mod = True

    db = MySQLdb.connect(host="47.93.192.232", user="root", passwd="sw64419", db="nebula", charset='utf8')
    cur = db.cursor()

    doJinkinsCoverage(cur)

    db.close()
