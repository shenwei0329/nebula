#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# XLSX 文件解析器
# ===============
# 2017年10月10日@成都
#
# 功能：通过解析xlsx文件，把记录数据导入数据库(MySQL)中，导入方式包括：更新/创建、追加。
#
# 2017.10.29：提供APPEND、UPDATE和ADD等三种操作方式，分别用于追加、更改和添加新纪录。
# 2017.11.3：增加测试数据统计；增加各个指标的统计时间区域【st_date,ed_date】
#
#

import sys
from DataHandler import main_month

reload(sys)
sys.setdefaultencoding('utf-8')

if __name__ == '__main__':

    main_month.main()

#
# Eof

