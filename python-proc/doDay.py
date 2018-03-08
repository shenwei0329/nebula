#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# XLSX 文件解析器
# ===============
# 2017年10月10日@成都
#
#   Usage: python doDay.py 开始日期 结束日期 工作日天数
#   【注意】：结束日期必须包含本周数据导入时间，例如今天（3月6日导入的周报数据，
#             则，结束日期为 xxxx-03-07
#
# 功能：通过解析xlsx文件，把记录数据导入数据库(MySQL)中，导入方式包括：更新/创建、追加。
#
# 2017.10.29：提供APPEND、UPDATE和ADD等三种操作方式，分别用于追加、更改和添加新纪录。
# 2017.11.3：增加测试数据统计；增加各个指标的统计时间区域【st_date,ed_date】
#
#

import os
import MySQLdb
import sys
from DataHandler import main

reload(sys)
sys.setdefaultencoding('utf-8')

if __name__ == '__main__':

    main.main()

#
# Eof

