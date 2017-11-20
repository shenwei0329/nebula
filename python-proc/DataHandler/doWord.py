# -*- coding: utf-8 -*-

import os
from wordHdler import easyWord
from xlsxHdler import easyExcel

def replaceWord(data, tmpl_path='d:/nebula/python-proc/word/week.docx', export_path=['export']):

        if os.path.exists(tmpl_path):
            w = easyWord()
            w.open(os.path.abspath(tmpl_path))
            print('open(%s)' % os.path.abspath(tmpl_path))
            for k in data:
                w.replaceAll('{{%s}}' % k, data[k])
            for ex in export_path:
                ex = os.path.join(os.path.abspath(ex), tmpl_path)
                if not os.path.exists(os.path.dirname(ex)):
                    os.makedirs(os.path.dirname(ex))
                print('output(%s)' % ex)
                w.saveAs(ex)
            w.close()
            w.quit()

"""
x = easyExcel(os.path.abspath('conf.xlsx'))

tmpl_path = []
while x.getCell('sheet1', len(tmpl_path)+2, 1):
    tmpl_path.append(x.getCell('sheet1', len(tmpl_path)+2, 1))

export_path = []
while x.getCell('sheet1', len(export_path)+2, 2):
    export_path.append(x.getCell('sheet1', len(export_path)+2, 2))

if not export_path:
    export_path = ['export']

data = {}
while x.getCell('sheet1', len(data)+2, 3):
    data[x.getCell('sheet1', len(data)+2, 3)] = x.getCell('sheet1', len(data)+2, 4)

x.close()
"""

replaceWord({'data1':'hello'})

