# -*- coding: utf-8 -*-

import os
import logging
import uuid

from os.path import getsize
from nebula.core.forms.form import NebulaForm
from wtforms import StringField
from wtforms import validators


from flask import request
from flask import jsonify

from nebula.core import constants
from nebula.core.managers import managers
from nebula.core.common.geventutils import save_file

from .base import SystemMixin
from nebula.portal.views.base import AuthorizedView

LOG = logging.getLogger(__name__)


class SystemSettingMixin(object):
    active_module = 'system_settings'


class SystemSettingForm(NebulaForm):
    system_title = StringField('system_title', validators=[validators.InputRequired()])
    system_copyright = StringField('system_copyright', validators=[validators.InputRequired()])

    def to_dict(self):
        data = {}
        for name, field in self._fields.iteritems():
            if name == 'csrf_token':
                continue
            data.update({
                name: field.data
            })
        LOG.error(data)
        return data


class SystemSettingView(SystemMixin, SystemSettingMixin, AuthorizedView):
    template_name = 'systems/system_settings.html'

    def get_context_data(self, **kwargs):
        context = super(SystemSettingView, self).get_context_data(**kwargs)
        context.update(dict(
            settings=managers.settings.get_settings(),
        ))
        return context

    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update(dict(form=SystemSettingForm()))
        return self.render_template(self.template_name, **context)

    def post(self, *args, **kwargs):
        form = SystemSettingForm()
        context = self.get_context_data(**kwargs)
        context.update(dict(
            form=form
        ))
        if form.validate():
            kwargs = form.to_dict()
            managers.settings.create_update_setting(**kwargs)
            context.update(dict(
                settings=managers.settings.get_settings(),
            ))
            return self.render_template(self.template_name, **context)
        return self.render_template(self.template_name, **context)

class SystemSetLogoForm(NebulaForm):
    system_logo = StringField('system_logo', validators=[validators.InputRequired()])
    system_logo_mini = StringField('system_logo_mini', validators=[validators.InputRequired()])
    system_logo_ico = StringField('system_logo_ico', validators=[validators.InputRequired()])

    def to_dict(self):
        data = {}
        for name, field in self._fields.iteritems():
            if name == 'csrf_token':
                continue
            data.update({
                name: field.data
            })
        LOG.error(data)
        return data




class SystemSetLogoView(SystemMixin, SystemSettingMixin, AuthorizedView):
    template_name = 'systems/system_set_logo.html'
    tpl_logo = "systems/form/upload_system_logo.html"

    def get_context_data(self, **kwargs):
        context = super(SystemSetLogoView, self).get_context_data(**kwargs)
        context.update(dict(
            settings=managers.settings.get_settings(),
        ))
        return context

    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update(dict(form=SystemSetLogoForm()))

        LOG.info("request.args.get('type') :%s" % request.args.get('type'))
        if request.args.get('type') == "mini":
            context.update(dict(type="mini"))
        elif request.args.get('type') == "ico":
            context.update(dict(type="ico"))
        else:
            context.update(dict(type="default"))

        return self.render_template(self.template_name if not request.args.get('type') else self.tpl_logo, **context)



    def post(self, *args, **kwargs):
        form = SystemSetLogoForm()
        context = self.get_context_data(**kwargs)
        context.update(dict(
            form=form
        ))
        if form.validate():
            kwargs = form.to_dict()
            managers.settings.create_update_setting(**kwargs)
            context.update(dict(
                settings=managers.settings.get_settings(),
            ))
            LOG.info("============")
            LOG.info(request.args)
            LOG.info(kwargs)
            if request.args.get('type'):
                return jsonify({"code": 0, "msg": "保存成功"})

            return self.render_template(self.template_name, **context)
        return self.render_template(self.template_name, **context)

#=========以下为上传logo图片
ALLOWED_EXTENSIONS = set(['png', 'gif', 'jpg', 'jpeg', 'ico'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def logo_upload(*args, **kwargs):
    """
    上传logo图片
    :return code: 0  成功 -1 失败
    """

    if request.method == 'POST':
        file = request.files['file']

        try:
            if file and allowed_file(file.filename):
                LOG.info(file.filename)
                file_name = str(uuid.uuid1()) + "." +file.filename.rsplit('.', 1)[1]
                file_path = os.path.join(constants.UPLOAD_SYSTEM_LOGO_FILE_PATH, file_name)

                LOG.info(file_path)

                save_file(file_path, file.stream)
                if os.path.exists(file_path):
                    #成功之后 检查是否是允许的格式
                    return jsonify({"code": 0, "data": {"file_name": os.path.join(constants.STATIC_LOGO_PATH, file_name), "size": getsize(file_path)}})
                return jsonify({"code": -1, "msg": "上传失败"})
            else:
                return jsonify({"code": -1, "msg": "上传的文件不存在或类型不允许"})
        except Exception as e:
            LOG.error("system logo upload is failed")
            LOG.error(e)
            return jsonify({"code": -1, "msg": "上传出现异常请稍后重试"})