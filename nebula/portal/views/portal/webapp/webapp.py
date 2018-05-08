# -*- coding: utf-8 -*-
__author__ = 'shenwei'

from flask import request
from nebula.core.views import TemplateView
from nebula.portal.views.portal.systems.base import SystemSW
from nebula.portal.utils.menu import setMenus
from flask.views import MethodView
from flask.ext.wtf import Form
from flask import jsonify, render_template, session, request, url_for, g
import os, json, urllib, urllib2

import logging

from oslo_config import cfg
CONF = cfg.CONF
CONF.import_group('webapp', 'nebula.portal.options')

LOG = logging.getLogger(__name__)

"""
本例采用了 FLASK 的表单扩展
"""
from wtforms import FileField, SubmitField
from wtforms.validators import Required
from nebula.portal.utils.menu import setMenus

class DIRView(MethodView):

    methods = ['GET', 'POST']

    _template_name = 'dir/dir.html'

    def get(self):
        context = dict(
            form=None,
            result=False,
        )
        context.update(setMenus())
        return render_template(self._template_name, **context)

    def post(self):

        context = dict(
            form=None,
            result=False,
        )
        context.update(setMenus())

        return render_template(self._template_name, **context)

class MusicFileForm(Form):
    filename = FileField(u'音乐文件', validators=[Required()])
    submit = SubmitField(u'提 交')

class MUSICView(MethodView):

    methods = ['GET', 'POST']

    _template_name = 'music/music.html'

    def get(self):
        context = dict(
            form=MusicFileForm(),
            result=False,
        )
        context.update(setMenus())
        return render_template(self._template_name, **context)

    def post(self):

        form = MusicFileForm()

        context = dict(
            form=form,
        )
        context.update(setMenus())

        if form.validate_on_submit():
            _filename = form.filename.data.filename
            _ext = _filename.split('.')[-1]
            _path = os.path.join(os.path.realpath('.') + '/static/', "_temp_music.%s" % _ext)
            form.filename.data.save(_path)
            _ret = json.loads(self.doCLI(_path))

            if _ret["status"] == 0:
                context['result'] = True
                context['file_name'] = _filename
                context['music_type'] = _ret['result']
                context['image_file'] = "%s.png"%_ret['result']

        return render_template(self._template_name, **context)

    def doCLI(self, _path):
        """
        执行一个CLI命令
        :param _path:
        :return:
        """

        """
        通过目录系统获取 音乐文件分类器 的URL
        """
        test_data = {'src-dir': _path}
        _url = 'http://localhost:8686/api/v1.0/posts/'
        if _url is not None:
            req_post_url = _url
            test_data_urlencode = urllib.urlencode(test_data)
            req = urllib2.Request(url=req_post_url, data=test_data_urlencode)
            res_data = urllib2.urlopen(req)
            res = res_data.read()
        else:
            res = {"status":1}

        return res

class RESTapiRegisterView(MethodView):

    methods = ['GET']

    template_name = 'webapp/webapp.html'

    def get(self):
        context = dict()
        context.update(setMenus())
        context.update(
            {'url': CONF.webapp.rest_api_register_web, }
        )
        return render_template(self.template_name, **context)
