# -*- coding: utf-8 -*-
__author__ = 'shenwei'

from flask import jsonify, render_template, request
from nebula.core.views import TemplateView
from nebula.portal.views.portal.systems.base import SystemSW
from nebula.portal.utils.menu import setMenus
from flask.ext.wtf import Form
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import Required
from flask.views import MethodView
import uuid,os
import logging

import sysv_ipc as ipc

from oslo_config import cfg

from nebula.core.managers.upfilemod import UpFileManager
from nebula.core.models.upfilemod import UpFileMod

try:
    q = ipc.MessageQueue(19640419001,ipc.IPC_CREAT | ipc.IPC_EXCL)
except:
    q = ipc.MessageQueue(19640419001)

CONF = cfg.CONF
CONF.import_group('webapp', 'nebula.portal.options')

LOG = logging.getLogger(__name__)

def getUUID():
    """
    获取UUID字符串
    :return:
        UUID
    """
    return str(uuid.uuid4())

class UpLoadForm(Form):
    filename = FileField(u'选择文件', validators=[Required()])
    desc = StringField(u'说明', validators=[Required()])
    version = StringField(u'版本', validators=[Required()])
    submit = SubmitField(u'提 交')

def getFileHash(fn):
    output = os.popen('md5sum %s' % fn)
    line = output.readline()
    return (line.split(' '))[0]

def submitForm():
    """
    处理SUBMIT事件

    :return:
        转向的HTML内容

    """

    global q

    context = dict(
        form=UpLoadForm()
    )
    context.update({
            "icon": "icon-folder-open",
            "title": u"数据导入：",
    })
    context.update(setMenus())

    form=UpLoadForm()
    if form.validate_on_submit():
        desc = form.desc.data
        version = form.version.data
        _filename = form.filename.data.filename
        _uuid = getUUID()
        _path = '/home/shenwei/nebula/static/etl_mod/%s'% _uuid
        form.filename.data.save(_path)

        f_hash = getFileHash(_path)
        param = {
            'desc': desc,
            'r_name': _filename,
            'filename': _uuid,
            'version': version,
            'f_hash': f_hash,
        }
        context['filename'] = _filename
        context['result'] = _filename

        upfile = UpFileManager(UpFileMod)
        """ 防止数据被重复录入：
            1）查看是否已经存在 该文件的 hash值
            2）若不存在，则说明：该文件未被录入；否则，表示该文件数据已录入
        """
        _hash = upfile.get(f_hash)
        if not _hash:
            upfile.create(_filename, **param)
            try:
                q.send(_path,block=False)
                context.update({'info': "已提交处理！"})
            except:
                context.update({'info': "文件处理出错：满了！"})

    return render_template('webapp/datain.html', **context)

class CDHListView(SystemSW, TemplateView):

    methods = ['GET', 'POST']
    template_name = 'webapp/datain.html'

    def get_context_data(self, **kwargs):

        context = super(CDHListView, self).get_context_data(**kwargs)
        cdh_id = request.args.get("resource_id", None)
        form = UpLoadForm()
        context.update({
            "resource_id": cdh_id,
            "icon": "icon-folder-open",
            "title": u"数据导入：",
            "form": form,
        })
        context.update(setMenus())
        return context

    def post(self):
        return submitForm()

class CDHChange(MethodView):

    methods = ['POST', 'GET']

    def get(self):
        """
        用于 列表翻页 的刷新

        :return:
        """
        context = dict(
            form=UpLoadForm(),
        )
        context.update(setMenus())

        return render_template('webapp/datain.html', **context)

    def post(self):
        """
        请求来自于：1）页面切换；2）定时器

        :return:
        """

        _value = int(request.json.get('value'))
        context = dict(
            form=UpLoadForm(),
        )
        context.update(setMenus())
        template_name = 'webapp/form/register.html'

        return jsonify(body=render_template(template_name, **context))

class CDHReport(MethodView):

    methods = ['POST']

    _template_name = 'webapp/form/register.html'

    def post(self):

        form = UpLoadForm()
        context = dict(
            form=form,
        )
        context.update(setMenus())

        return jsonify(body=render_template(self._template_name, **context))

