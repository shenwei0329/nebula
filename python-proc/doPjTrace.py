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

    if len(sys.argv) <= 2:
        if len(sys.argv) == 2:
            plans2018.main(project_alias=sys.argv[1])
        else:
            plans2018.main()
    else:
        print("\n\tUsage: python %s project_name\n" % sys.argv[0])

#
# Eof

