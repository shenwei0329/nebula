#!/usr/bin/env python
#coding=utf-8

import os

def scan_files(directory,prefix=None,postfix=None):
    files_list=[]
    
    for root, sub_dirs, files in os.walk(directory):
        for special_file in files:
            if postfix:
                if special_file.endswith(postfix):
                    files_list.append(os.path.join(root,special_file))
            elif prefix:
                if special_file.startswith(prefix):
                    files_list.append(os.path.join(root,special_file))
            else:
                files_list.append(os.path.join(root,special_file))
                          
    return files_list

if __name__ == '__main__':

    f_list = scan_files('d:\\cygwin64\\home\\shenw\\upload_dir')

    for _f in f_list:
        _cmd = 'curl -F "file=@%s" http://47.93.192.232:5010/upload -X POST' % _f
        #print _cmd
        os.system(_cmd)

        _cmd = 'rm %s' % _f
        #print _cmd
        os.system(_cmd)
