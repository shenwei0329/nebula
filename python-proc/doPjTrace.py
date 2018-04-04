#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# 项目计划跟踪报告生成器
# ======================
# 2017年12月8日@成都
#
#
import sys
from DataHandler import plans2018

reload(sys)
sys.setdefaultencoding('utf-8')

if __name__ == '__main__':

    if len(sys.argv) in [4, 5]:
        if len(sys.argv) == 5:
            _week_end = False
            if sys.argv[2] == 'eow':
                _week_end = True
            plans2018.main(project=sys.argv[1], project_alias=sys.argv[2], landmark_id=sys.argv[3], week_end=_week_end)
        else:
            plans2018.main(project=sys.argv[1], project_alias=sys.argv[2], landmark_id=sys.argv[3], week_end=False)
    else:
        print("\n\tUsage: python %s project project_alias landmark_id [eow]\n" % sys.argv[0])

#
# Eof

