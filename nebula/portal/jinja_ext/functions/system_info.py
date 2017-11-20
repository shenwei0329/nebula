# -*- coding: utf-8 -*-

def systeminfo(key, default="default"):
    return default

if __name__ == '__main__':
    from nebula.core import config
    config.set_defaults(args=[], prog='blah')
    print(systeminfo("system_copyright"))
    print(systeminfo("system_cht"))