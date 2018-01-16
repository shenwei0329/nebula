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

todos = {}

class TodoSimple(Resource):
    def __init__(self):
        try:
            self.q = ipc.MessageQueue(19640419001, ipc.IPC_CREAT | ipc.IPC_EXCL)
        except:
            self.q = ipc.MessageQueue(19640419001)

    def get(self, todo_id):
        return {todo_id: todos[todo_id]}

    def put(self, todo_id):
        todos[todo_id] = request.form['filename']
        self.q.send(_path, block=False)
        return {todo_id: todos[todo_id]}

@app.route('/upload', methods=['POST'])
def upload():
    upload = request.files['file']

    print upload

    if upload:
        filename = upload.filename

        print filename
        
        upload.save(os.path.join('downloads', filename))
        app.logger.debug('File is saved as %s', filename)

api.add_resource(TodoSimple, '/<string:todo_id>')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5010)