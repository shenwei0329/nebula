# -*- coding: utf-8 -*-
#

from docx import Document
from docx.shared import Pt
from docx.shared import Inches
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

class createWord:

    def __init__(self):
        self.document = Document()
        self.document.styles['Normal'].font.name = u'微软黑体'
        self.document.styles['Normal'].paragraph_format.space_before = Pt(10)
        self.document.styles['Normal'].paragraph_format.space_after = Pt(10)
        self.document.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), u'微软黑体')
        self.document.styles['Title'].font.name = u'微软黑体'
        self.document.styles['Heading1'].font.name = u'微软黑体'
        self.document.styles['Heading2'].font.name = u'微软黑体'
        self.document.styles['Heading3'].font.name = u'微软黑体'

    def addHead(self, info, lvl, align=WD_ALIGN_PARAGRAPH.LEFT):
        _style = 'Title' if lvl == 0 else 'Heading%d' % lvl
        _paragraph = self.document.add_paragraph(info, _style)
        _paragraph.paragraph_format.alignment = align

    def addText(self, info, align=WD_ALIGN_PARAGRAPH.LEFT):
        self.paragrap = self.document.add_paragraph(info)
        self.paragrap.paragraph_format.alignment = align
        self.paragrap.paragraph_format.first_line_indent = Inches(0.3)

    def addPic(self, pic_path, sizeof=5):
        self.paragrap = self.document.add_paragraph()
        self.paragrap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run = self.paragrap.add_run()
        _run.add_picture(pic_path, width=Inches(sizeof))

    def addTable(self, n_rows, n_cols, data):
        _table = self.document.add_table(rows=n_rows, cols=n_cols)
        for _idx in range(n_rows):
            _hdr_cells = _table.rows[_idx].cells
            for __idx in range(n_cols):
                _hdr_cells[__idx].text = data[_idx][__idx]

    def addPageBreak(self):
        self.document.add_page_break()

    def saveFile(self, fname):
        self.document.save(fname)

#
#