#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# REST ful接口
# ==============
# 2018年1月15日@成都
#
#

from flask import Flask, request
from flask.ext.restful import Resource, Api
import sysv_ipc as ipc
import os

app = Flask(__name__)
api = Api(app)

@app.route('/upload', methods=['POST'])
def upload():
    upload = request.files['file']

    if upload:
        filename = upload.filename
        upload.save(os.path.join('downloads', filename))
        app.logger.debug('File is saved as %s', filename)
        try:
            q = ipc.MessageQueue(19640419001, ipc.IPC_CREAT | ipc.IPC_EXCL)
        except:
            q = ipc.MessageQueue(19640419001)
        q.send('/home/shenwei/nebula/python-proc/downloads/%s' % filename, block=False)
        return "Done"

    return "Error"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5010)