#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-

import sys, os, uuid, locale, json

reload(sys)
sys.setdefaultencoding('utf-8')

dirList = [
    u'基础数据',
    u'周报数据',
    u'考勤数据',
]

file_hash_list = {}

def getFileHash(fn):

    _cmd = (u'md5sum %s' % fn).encode(locale.getdefaultlocale()[1])
    output = os.popen(_cmd)
    line = output.readlines()
    if len(line)>0:
        return (line[0].split(' '))[0].replace('\\','')
    return ""

def scan_files(directory,prefix=None,postfix=None):

    files_list=[]
    
    for root, sub_dirs, files in os.walk(directory):
        for special_file in files:
            if postfix:
                if special_file.endswith(postfix):
                    files_list.append(os.path.join(root, special_file))
            elif prefix:
                if special_file.startswith(prefix):
                    files_list.append(os.path.join(root, special_file))
            else:
                files_list.append(os.path.join(root, special_file))

    return files_list

if __name__ == '__main__':

    f = open('D:\\cygwin64\\home\\shenw\\filehash.txt', 'r')
    s = f.read()
    file_hash_list = json.loads(s)
    f.close()

    for _dir in dirList:

        f_list = scan_files(u'D:\\shenwei\\2017-华云\\研发管理数据\\%s' % _dir)

        for _f in f_list:
            if ('.xlsx' in _f) and (u'【模板】' in _f) and ('~$' not in _f):
                _updated = False
                _hash = getFileHash(_f)
                if _f not in file_hash_list:
                    file_hash_list[_f] = _hash
                    _updated = True
                else:
                    if file_hash_list[_f] != _hash:
                        file_hash_list[_f] = _hash
                        _updated = True
                if _updated:
                    _fn = 'D:\\cygwin64\\home\\shenw\\upload_dir\%s' % str(uuid.uuid4())
                    _cmd = (u'cp %s %s' % (_f, _fn)).encode(locale.getdefaultlocale()[1])
                    print _cmd
                    os.system(_cmd)

    f = open('D:\\cygwin64\\home\\shenw\\filehash.txt','w')
    s = json.dumps(file_hash_list)
    f.write(s)
    f.close()
