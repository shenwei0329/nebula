# -*- coding: utf-8 -*-
from nebula.core.i18n import _
import math

_B = _(u"B")
_KB = _(u"KB")
_MB = _(u"MB")
_GB = _(u"GB")
_TB = _(u"TB")
_PB = _(u"PB")

def bt_to_g(bytes):
    if isinstance(bytes, basestring):
        bytes = int(bytes)
    return math.ceil(bytes/1024.0/1024/1024*100)/100

def human_size(size_bytes):
    """
    format a size in bytes into a 'human' file size, e.g. bytes, KB, MB, GB, TB,
    PB
    Note that bytes/KB will be reported in whole numbers but MB and above will
    have greater precision e.g. 1 byte, 43 bytes, 443 KB, 4.3 MB, 4.43 GB, etc
    """
    if size_bytes == 1:
        # because I really hate unnecessary plurals
        return "1 byte"

    suffixes_table = [(_B, 0), (_KB, 0), (_MB, 1), (_GB, 2), (_TB, 2),
                      (_PB, 2)]

    num = float(size_bytes)
    for suffix, precision in suffixes_table:
        if num < 1024.0:
            break
        num /= 1024.0

    if precision == 0:
        formatted_size = "%d" % num
    else:
        formatted_size = str(round(num, ndigits=precision))

    return "%s %s" % (formatted_size, suffix)


def percent(total, used):
    if total == 0:
        return 0
    return int( float(used) / float(total) * 100)
