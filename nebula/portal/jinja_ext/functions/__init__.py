# -*- coding: utf-8 -*-
import hashlib
import os
from flask import current_app

from nebula import version
from nebula.portal.jinja_ext.functions.system_info import systeminfo


def static_url(filename):
    if current_app.testing:
        return filename

    if not hasattr(current_app, '_static_hash'):
        # 若当前APP没有_static_hash列表，则分配一个
        current_app._static_hash = {}

    if filename in current_app._static_hash:
        # 若获取的文件包含在列表中，则直接返回
        return current_app._static_hash[filename]

    with open(os.path.join(current_app.static_folder, filename), 'r') as f:
        # 计算HASH
        content = f.read()
        hsh = hashlib.md5(content).hexdigest()

    current_app.logger.info('Generate %s md5sum: %s' % (filename, hsh))
    prefix = current_app.config.get
    value = '%s%s?v=%s' % (prefix, filename, hsh[:12])

    # 把该文件的属性放入列表中
    current_app._static_hash[filename] = value
    return value


def register_functions(app):

    # 设置一种方法，用于获取一个URL
    app.jinja_env.globals['static_url'] = static_url
    app.jinja_env.globals['version'] = version
    app.jinja_env.globals['systeminfo'] = systeminfo
