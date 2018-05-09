#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#   根据jenkins记录数据生成测试覆盖率示意图
#   =======================================
#

import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.dates import AutoDateLocator, DateFormatter
from pylab import figure, axes
import MySQLdb, sys, time
import matplotlib.pyplot as plt

_test_mod = False

reload(sys)
sys.setdefaultencoding('utf-8')

def doSQL(cur,_sql):

    cur.execute(_sql)
    return cur.fetchall()

def doJinkinsCoverage(cur, pj_id):
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

    """条件获取数据"""
    _sql = 'select filename,line_rate,branch_rate,complexity from jenkins_coverage_t ' \
           'where pj_id="%s" and filename<>"#" and filename like "%%Controller.java%%"' % pj_id
    _res = doSQL(cur, _sql)

    if len(_res) == 0:
        return None

    _max = 0.
    for _r in _res:
        _fn = _r[0][_r[0].rfind('/')+1:]
        _filename.append(_fn)
        _line_rate += (float(_r[1]),)
        _branch_rate += (-float(_r[2]),)
        __complexity += (float(_r[3]),)
        if float(_r[3]) > _max:
            _max = float(_r[3])

    """调整显示比例"""
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

    """按比例作图"""
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
    plt.ylim(-1.1, 1.6)

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
