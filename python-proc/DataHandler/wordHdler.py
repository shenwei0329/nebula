# -*- coding: utf-8 -*-

import win32com.client
import os
#--------------------------------------------------------------------------
class easyWord:
    '''
    Some convenience methods for Excel documents accessed
    through COM.
    '''
    def __init__(self,visible=False):
        print(">>>easyWord.init")
        self.wdApp = win32com.client.DispatchEx('Word.Application')
        self.wdApp.Visible = visible
        self.wdApp.DisplayAlerts = False

    def new(self,filename=None):
        print(">>>easyWord.new[%s]" % filename)
        '''
        Create a new Word document. If 'filename' specified,
        use the file as a template.
        '''
        if filename:
            return self.wdApp.Documents.Add(filename)
        else:
            return self.wdApp.Documents.Add()

    def open(self,filename):
        print(">>>easyWord.open[%s]" % filename)
        '''
        Open an existing Word document for editing.
        '''
        return self.wdApp.Documents.Open(filename)

    def visible(self,visible=True):
        self.wdApp.Visible = visible

    def find(self,text,MatchWildcards=False):
        print(">>>easyWord.find")
        '''
        Find the string
        '''
        find = self.wdApp.Selection.Find
        find.ClearFormatting()
        find.Execute(text, False, False, MatchWildcards, False, False, True, 0)
        return self.wdApp.Selection.Text

    def replaceAll(self,oldStr,newStr):
        print(">>>easyWord.replaceAll[%s:%s]" % (oldStr, newStr))
        '''
        Find the oldStr and replace with the newStr.
        '''
        find = self.wdApp.Selection.Find
        find.ClearFormatting()
        find.Replacement.ClearFormatting()
        find.Execute(oldStr, False, False, False, False, False, True, 1, True, newStr, 2)

    def updateToc(self):
        for tocitem in self.wdApp.ActiveDocument.TablesOfContents:
            tocitem.Update()

    def save(self):
        print(">>>easyWord.save")
        '''
        Save the active document
        '''
        self.wdApp.ActiveDocument.Save()

    def saveAs(self,filename,delete_existing=True):
        print(">>>easyWord.saveAs[%s]" % filename)
        '''
        Save the active document as a different filename.
        If 'delete_existing' is specified and the file already
        exists, it will be deleted before saving.
        '''
        if delete_existing and os.path.exists(filename):
            os.remove(filename)
        self.wdApp.ActiveDocument.SaveAs(FileName=filename)

    def close(self):
        '''
        Close the active workbook.
        '''
        self.wdApp.ActiveDocument.Close()

    def quit(self):
        '''
        Quit Word
        '''
        return self.wdApp.Quit()