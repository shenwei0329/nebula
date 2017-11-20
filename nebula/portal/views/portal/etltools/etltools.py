# -*- coding: utf-8 -*-
"""
    ETL处理程序

    2015.7.27 shenwei @ChengDu

    需要解决的问题：

    1）数据库访问机制，表记录创建；用列表显示
    2）ETL模型列表及其操作（更名、删除等）
    3）列表显示“在线”作业，含状态

    2015.8.30
    － 对程序进行标注、整理
    － 完成ETL任务管理（含状态显示）

    2015.11.7
    - 在此基础上，改为“资源管理”

"""

__author__ = 'shenwei'

from nebula.core.views import TemplateView
import os
import logging
import urllib
import urllib2
import json

from nebula.core.managers.etlmod import EtlManager
from flask.ext.paginate import Pagination
from nebula.portal.utils.menu import setMenus

from nebula.core.models.etlmod import EtlDir, EtlServer, EtlMod, EtlTask, EtlJob

from flask import jsonify, render_template, request
from flask.views import MethodView

from flask.ext.wtf import Form
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import Required

import uuid

LOG = logging.getLogger(__name__)

from oslo_config import cfg

CONF = cfg.CONF
CONF.import_group('webapp', 'nebula.portal.options')

'''
UI FORM模板
'''
class DirForm(Form):
    name = StringField(u'名称', validators=[Required()])
    desc = StringField(u'说明', validators=[Required()])
    submit = SubmitField(u'提 交')

class UpLoadForm(Form):
    filename = FileField(u'选择文件', validators=[Required()])
    name = StringField(u'名称', validators=[Required()])
    desc = StringField(u'说明', validators=[Required()])
    cmd = StringField(u'执行脚本', validators=[Required()])
    version = StringField(u'版本', validators=[Required()])
    submit = SubmitField(u'提 交')

class ServerRegisterForm(Form):
    name = StringField(u'名称', validators=[Required()])
    desc = StringField(u'说明', validators=[Required()])
    url = StringField(u'访问路径', validators=[Required()])
    submit = SubmitField(u'提 交')

class TaskForm(Form):
    name = StringField(u'任务名称', validators=[Required()])
    mod = StringField(u'模型', validators=[Required()])
    server = StringField(u'服务器', validators=[Required()])
    submit = SubmitField(u'提 交')

class JobForm(Form):
    name = StringField(u'作业名称', validators=[Required()])
    mod = StringField(u'模型', validators=[Required()])
    server = StringField(u'服务器', validators=[Required()])
    schedule = StringField(u'调度策略：M分 H时 D日 m月 d周', validators=[Required()])
    submit = SubmitField(u'提 交')

"""
初始化环境变量

    _etl_page：      页面索引［0～］
    _status：    页面状态［0:列表，1:创建记录，］

    ETL_ENTRY：  ETL页面个数
    N_PAGE：     每页列表的记录个数，缺省为16个

"""

_etl_page = 0
_status = []
_page_idx = []
MAX_ENTRY = 5
N_PAGE = 10
for i in range(0, MAX_ENTRY):
    _status.append({})
    _status[i]['do'] = 0
    _status[i]['filename'] = ""
    _status[i]['info'] = u"欢迎光临"
    _page_idx.append(1)
_task_log = []
_job_log = []

'''2015-9-22 by shenwei @chengdu
    引入 LDAP 模块
'''
#from nebula.utils.tools.ldap_api import LDAP
#_my_ldap = LDAP(CONF.webapp.ldap_server_host, CONF.webapp.ldap_user, CONF.webapp.ldap_passwd)

"""
公共API
"""
def getUUID():
    """
    获取UUID字符串
    :return:
        UUID
    """
    return str(uuid.uuid4())

def getStatus(entry):
    """
    获取页面的状态

    :param entry:
    :return:
    """
    global _status, _etl_page
    return _status[_etl_page][entry]

def setStatus(entry, value):
    """
    设置页面的状态

    :param entry:
    :param value:
    :return:
    """
    global _status, _etl_page
    _status[_etl_page][entry] = value

def getList(model):
    """
    获取数据模型的列表

    :param model:
    :return:
    """

    global _page_idx, _etl_page

    if model == EtlDir:
        model_name = u'资源目录'
    elif model == EtlMod:
        model_name = u'资源列表'
    elif model == EtlServer:
        model_name = u'服务器'
    elif model == EtlTask:
        model_name = u'任务'
    elif model == EtlJob:
        model_name = u'作业'
    _rec = getAll(model)

    page = _page_idx[_etl_page]

    _index = (page-1) * 10
    _next = _index + 10
    if _next > len(_rec):
        """ 2015.9.15 by shenwei @chengdu
            当本页面内容被删完时，应转到上一页
        """
        if len(_rec[_index:])==0 and page>1:
            page -= 1
            _page_idx[_etl_page] = page
        _posts = _rec[_index:]
    else:
        _posts = _rec[_index:_next]

    pagination = Pagination(page=page, total=len(_rec), record_name=model_name, css_framework='foundation')
    return pagination, _posts

def getAll(model):
    """
    获取数据模板的所有数据记录

    :param model:
    :return:
    """

    etl = EtlManager(model)
    _recs = etl.list()

    if _recs == None:
        return None

    _posts = []

    for _rec in _recs:
        _post = {}
        _post['name'] = _rec.name
        if model == EtlDir:
            _post['desc'] = _rec.desc
            _post['uuid'] = _rec.dir
            _post['created_at'] = _rec.created_at
        elif model == EtlServer:
            _post['desc'] = _rec.desc
            _post['url'] = _rec.url
            _post['status'] = _rec.status
            _post['created_at'] = _rec.created_at
        elif model == EtlMod:
            _post['desc'] = _rec.desc
            _post['r_name'] = _rec.r_name
            _post['uuid'] = _rec.filename
            _post['cmd'] = _rec.cmd
            _post['version'] = _rec.version
            _post['created_at'] = _rec.created_at
        elif model == EtlTask:
            _post['mod'] = _rec.mod
            _post['server'] = _rec.server
            _post['created_at'] = _rec.created_at
            _post['status'] = _rec.status
        elif model == EtlJob:
            _post['mod'] = _rec.mod
            _post['server'] = _rec.server
            _post['schedule'] = _rec.schedule
            _post['created_at'] = _rec.created_at
            _post['status'] = _rec.status
        _posts.append(_post)
    return _posts

def updateTaskStatus(task_name, status):
    """

    根据返回状态修改数据模型中的status

    0～20：步进5（约20秒）；21～40：步进3（约35秒）；41～60：步进2（约50秒）；61～80：步进1（约100秒）；81～99：步进1（约100秒）；99：不变

    :return:
    """
    etl = EtlManager(EtlTask)
    _rec = etl.get(task_name)
    if _rec is not None:
        _sts = _rec['status']
        if status != _sts:
            if status == 'RUNNING':
                if _sts=='DONE' or _sts=='ERROR':
                    _sts = '100'
                _st = int(_sts)
                if _st<21:
                    _st += 5
                elif _st<41:
                    _st += 3
                elif _st<99:
                    _st += 1
                val = {'status': str(_st)}
            elif status == 'DONE':
                val = {'status': 'DONE'}
            else:
                val = {'status': 'ERROR'}
            etl = EtlManager(EtlTask)
            etl.update(task_name, **val)

def updateJobStatus(job_name, status):
    """

    根据返回状态修改数据模型中的status

    0～20：步进5（约20秒）；21～40：步进3（约35秒）；41～60：步进2（约50秒）；61～80：步进1（约100秒）；81～99：步进1（约100秒）；99：不变

    :return:
    """
    etl = EtlManager(EtlJob)
    _rec = etl.get(job_name)
    if _rec is not None:
        _sts = _rec['status']
        if status != _sts:
            if status == 'RUNNING':
                if _sts=='DONE' or _sts=='ERROR':
                    _sts = '100'
                elif _sts=='SCHEDULE':
                    _sts = '0'
                _st = int(_sts)
                if _st<21:
                    _st += 5
                elif _st<41:
                    _st += 3
                elif _st<99:
                    _st += 1
                val = {'status': str(_st)}
            elif status == 'DONE':
                val = {'status': 'DONE'}
            elif status == 'SCHEDULE':
                val = {'status': 'SCHEDULE'}
            else:
                val = {'status': 'ERROR'}
            etl = EtlManager(EtlJob)
            etl.update(job_name, **val)

def setTaskStatus(task_name, status):
    etl = EtlManager(EtlTask)
    _rec = etl.get(task_name)
    if _rec is not None:
        val = {'status': status}
        etl = EtlManager(EtlTask)
        etl.update_by_name(task_name, **val)

def setJobStatus(job_name, status):
    etl = EtlManager(EtlJob)
    _rec = etl.get(job_name)
    if _rec is not None:
        val = {'status': status}
        etl = EtlManager(EtlJob)
        etl.update_by_name(job_name, **val)

def rest_get_url(api):
    """
    通过REST接口注册服务获取 API 的URL

    2015-09-22 by shenwei @chengdu
    - 将接口改为 LDAP 模式

    :param api:
    :return:
    """
    """
    params = urllib.urlencode({'name': api})
    _url = CONF.webapp.rest_api_register
    _f = urllib.urlopen("%s?%s" % (_url,params))
    res_data = json.loads(_f.read())
    if res_data.has_key('url'):
        return res_data['url']
    else:
        return ''
    global _my_ldap
    return _my_ldap.get_rest_api(api)
    """
    return "http://localhost:8686/api/v1.0/"+api

def rest_get_task_status(url):
    """
    通过REST接口获取 ETL任务 的执行状态

    返回参数：
    {
        "任务1":"DONE",
        "任务2":"ERROR",
        ...
        "任务?":"RUNNING",
        ...
    }

    :param url:
    :return:
    """

    req = urllib2.Request(url=url)
    res_data = urllib2.urlopen(req)
    _res = res_data.read()
    return json.loads(_res)

def rest_get_task_log(url, task_name):
    """
    通过REST接口获取 ETL任务 的日志

    返回参数：
    {
        "text":"日志文件的内容",
    }

    :param url:
    :param task_name:
    :return:
    """

    _url = url + '?task-name=' + task_name
    req = urllib2.Request(url=_url)
    res_data = urllib2.urlopen(req)
    _res = res_data.read()
    return json.loads(_res)

def rest_get_job_log(url, job_name):
    """
    通过REST接口获取 ETL作业 的日志

    返回参数：
    {
        "text":"日志文件的内容",
    }

    :param url:
    :param task_name:
    :return:
    """

    _url = url + '?job-name=' + job_name
    req = urllib2.Request(url=_url)
    res_data = urllib2.urlopen(req)
    _res = res_data.read()
    return json.loads(_res)

def submitForm():
    """
    处理SUBMIT事件

    :return:
        转向的HTML内容

    """

    global _status, _etl_page

    context = dict(
        form=setForm(_etl_page),
        result=False,
        etl_page=_etl_page,
        etl_href="etl_mod_post",
        etl_do=getStatus('do'),
        etl_png="../static/etl.jpg",
        etl_info=getStatus('info'),
    )
    context.update(setMenus())

    if _etl_page == 0:
        """资源目录
        """
        form = DirForm()
        context['form'] = form
    elif _etl_page == 1:
        """资源
        """
        form = UpLoadForm()
        context['form'] = form
    elif _etl_page == 2:
        """任务
        """
        form = TaskForm()
        context['form'] = form
    elif _etl_page == 3:
        """作业
        """
        form = JobForm()
        context['form'] = form

    if form.validate_on_submit():
        if _etl_page == 0:
            name = form.name.data
            desc = form.desc.data
            param = {
                    'desc': desc,
                    'dir': getUUID(),
                    }
            etl = EtlManager(EtlDir)
            _rec = etl.get(name)
            if _rec == None:
                etl.create(name, **param)
                """!!!创建目录
                """
                setStatus('info', u"")
                context['etl_info'] = getStatus('info')
                setStatus('do', 0)
                context['etl_do'] = getStatus('do')
            else:
                setStatus('info',u"错误：该资源目录名称已经存在！")
                context['etl_info'] = getStatus('info')
        elif _etl_page == 1:
            name = form.name.data
            desc = form.desc.data
            cmd = form.cmd.data
            version = form.version.data
            _filename = form.filename.data.filename
            param = {
                'desc': desc,
                'r_name': _filename,
                'filename': getUUID(),
                'cmd': cmd,
                'version': version,
            }
            context['filename'] = _filename
            etl = EtlManager(EtlMod)
            _rec = etl.get(name)
            if _rec == None:
                _path = '/home/shenwei/nebula/static/etl_mod/'+param['filename']
                form.filename.data.save(_path)
                context['result'] = _filename
                setStatus('filename',_filename)
                context['etl_page'] = _etl_page
                context['etl_do'] = getStatus('do')
                context['filename'] = _filename

                etl.create(name, **param)

                setStatus('info', u"")
                context['etl_info'] = getStatus('info')
                setStatus('do', 0)
                context['form'] = UpLoadForm()
                context['etl_do'] = getStatus('do')
            else:
                setStatus('info',u"错误：该模块名称已经存在！")
                context['etl_info'] = getStatus('info')
                setStatus('info', u"")
        elif _etl_page == 2:
            name = form.name.data
            mod = form.mod.data
            server = form.server.data
            param = {
                'mod': mod,
                'server': server,
                'status': '0'   # 新任务的工作进度为 0
            }
            """ 查看该名称已使用？
            """
            etl = EtlManager(EtlTask)
            _rec = etl.get(name)
            if _rec == None:
                """ 新任务创建完成，需把任务请求发给指定的ETL服务器执行。
                1）用scp拷贝模型到指定ETL服务器的模型目录；
                2）调用该ETL服务器的REST API发起任务请求。
                """
                context['etl_page'] = _etl_page
                etl.create(name, **param)

                setStatus('info', u"")
                context['etl_info'] = getStatus('info')
                setStatus('do', 0)
                context['form'] = TaskForm()
                context['etl_do'] = getStatus('do')
            else:
                setStatus('info',u"错误：该模块名称已经存在！")
                context['etl_info'] = getStatus('info')
                setStatus('info', u"")
        elif _etl_page == 3:
            name = form.name.data
            mod = form.mod.data
            server = form.server.data
            schedule = form.schedule.data
            param = {
                'mod': mod,
                'server': server,
                'schedule': schedule,
                'status': '0',  # 新作业的工作进度为 0
            }
            etl = EtlManager(EtlJob)
            _rec = etl.get(name)
            if _rec == None:
                """新作业创建完成，需把任务请求发给指定的ETL服务器执行。
                1）用scp拷贝模型到指定ETL服务器的模型目录；
                2）调用该ETL服务器的REST API发起任务请求。
                """
                context['etl_page'] = _etl_page
                etl.create(name, **param)

                setStatus('info', u"")
                context['etl_info'] = getStatus('info')
                setStatus('do', 0)
                context['form'] = JobForm()
                context['etl_do'] = getStatus('do')
            else:
                setStatus('info',u"错误：该模块名称已经存在！")
                context['etl_info'] = getStatus('info')
                setStatus('info', u"")
    else:

        setStatus('do', 0)
        context['etl_do'] = getStatus('do')

    if _etl_page == 0:
        _page, _info = getList(EtlDir)
        context['pagination'] = _page
        context['dirs'] = _info

    elif _etl_page == 1:
        _page, _info = getList(EtlMod)
        context['pagination'] = _page
        context['mods'] = _info

    elif _etl_page == 2:
        _page, _info = getList(EtlTask)
        context['pagination'] = _page
        context['tasks'] = _info

    elif _etl_page == 3:
        _page, _info = getList(EtlJob)
        context['pagination'] = _page
        context['jobs'] = _info

    return render_template('etltools/etlbase.html', **context)

class ETLToolsGetPage(MethodView):
    """
    GET请求：用于获取ETL的工作页面 _etl_page
    """
    methods = ['GET']

    def get(self):
        global _etl_page
        return jsonify({'etl_page': _etl_page, 'etl_sub_step': getStatus('do')})

class ETLToolsView(MethodView):
    """
    GET请求：获取页面内容
    POST请求：提交页面记录
    """

    methods = ['GET', 'POST']

    _template_name = 'etltools/etlbase.html'

    def get(self):

        global _status, _etl_page

        try:
            _page_idx[_etl_page] = int(request.args.get('page', 1))
        except ValueError:
            _page_idx[_etl_page] = 1
        finally:

            context = dict(
                result=False,
                form=setForm(_etl_page),
                etl_page=_etl_page,
                etl_href="etl_mod_post",
                etl_body=True,
                etl_do=getStatus('do'),
                filename=getStatus('filename'),
                etl_info=getStatus('info'),
                etl_png="../static/etl.jpg",
            )
            context.update(setMenus())

            """ 获取UI的当前页面，并获取该页面对应数据模型的记录数据（供列表显示）
            """
            _page = request.args.get('etl_app')
            if _page == 'etl_mod_post':
                _etl_page = 1
                _page, _info = getList(EtlMod)
                context['pagination'] = _page
                context['tasks'] = _info
            elif _page == 'etl_pen_post':
                _etl_page = 2
                _page, _info = getList(EtlTask)
                context['pagination'] = _page
                context['tasks'] = _info
            elif _page == 'etl_scheduler_post':
                _etl_page = 3
                _page, _info = getList(EtlJob)
                context['pagination'] = _page
                context['jobs'] = _info
            else:
                _etl_page = 0
                _page, _info = getList(EtlDir)
                context['pagination'] = _page
                context['dirs'] = _info

            setStatus('do', 0)
            context['etl_page'] = _etl_page

            return render_template(self._template_name, **context)

    def post(self):

        return submitForm()

def setForm(step):

    if step == 0:
        form = DirForm()
    elif step == 1:
        form = UpLoadForm()
    elif step == 2:
        form = TaskForm()
    else:
        form = JobForm()
    return form

class ETLReport(MethodView):
    """
    2015.7.29 shenwei @chengdu
    这是一个处理 jQuery 请求的服务
    """

    methods = ['POST']

    _template_name = 'etltools/form/register.html'

    def post(self):

        global _etl_page, _status

        _etl_page = int(request.json.get('value'))

        form = setForm(_etl_page)

        context = dict(
            result=False,
            form=form,
            etl_page=_etl_page,
            etl_href="etl_mod_post",
            etl_do=getStatus('do'),
            etl_png="../static/etl.jpg",
            etl_info=getStatus('info')
        )
        context.update(setMenus())

        return jsonify(body=render_template(self._template_name, **context))

class ETLChange(MethodView):
    """
    2015.8.12 shenwei @chengdu
    """

    methods = ['POST', 'GET']

    def get(self):
        """
        用于 列表翻页 的刷新

        :return:
        """
        global _status, _page_idx, _task_log, _etl_page

        try:
            _page_idx[_etl_page] = int(request.args.get('page', 1))
        except ValueError:
            _page_idx[_etl_page] = 1
        finally:

            context = dict(
                form=setForm(_etl_page),
                result=False,
                etl_page=_etl_page,
                etl_href="etl_mod_post",
                etl_do=getStatus('do'),
                etl_png="../static/etl.jpg",
                etl_info=getStatus('info')
            )
            context.update(setMenus())

            if _etl_page == 0:
                _page, _info = getList(EtlDir)
                context['pagination'] = _page
                context['dirs'] = _info

            elif _etl_page == 1:
                _page, _info = getList(EtlMod)
                context['pagination'] = _page
                context['mods'] = _info

            elif _etl_page == 2:
                _page, _info = getList(EtlTask)
                context['pagination'] = _page
                context['tasks'] = _info

                context['text'] = _task_log

            elif _etl_page == 3:
                _page, _info = getList(EtlJob)
                context['pagination'] = _page
                context['jobs'] = _info

                context['text'] = _job_log

            return render_template('etltools/etlbase.html', **context)

    def post(self):
        """
        请求来自于：1）页面切换；2）定时器

        :return:
        """

        global _status, _task_log, _job_log, _etl_page

        try:
            _value = int(request.json.get('value'))
            if _value <= 3:
                _etl_page = _value
                if _etl_page == 2:
                    """ 收集 ETL任务 的执行状态
                    """
                    _url = rest_get_url('etl-task-status/')
                    if _url != '':
                        _sts = rest_get_task_status(_url)
                        for _st in _sts:
                            """ 根据返回的任务状态［组］修改数据模型中的 status 值
                                为体现良好的UI体验，任务进度采用log函数效果（前端快，后端缓慢）
                                0～20：步进5（约20秒）；21～40：步进3（约35秒）；41～60：步进2（约50秒）；61～80：步进1（约100秒）；81～99：步进1（约100秒）；99：不变
                            """
                            updateTaskStatus(_st, _sts[_st])
                elif _etl_page == 3:
                    """ 收集 ETL作业 的执行状态
                    """
                    _url = rest_get_url('etl-job-status/')
                    if _url != '':
                        _sts = rest_get_task_status(_url)
                        for _st in _sts:
                            """ 根据返回的任务状态［组］修改数据模型中的 status 值
                                为体现良好的UI体验，任务进度采用log函数效果（前端快，后端缓慢）
                                0～20：步进5（约20秒）；21～40：步进3（约35秒）；41～60：步进2（约50秒）；61～80：步进1（约100秒）；81～99：步进1（约100秒）；99：不变
                            """
                            updateJobStatus(_st, _sts[_st])
        except Exception:
            return submitForm()

        context = dict(
            form=setForm(_etl_page),
            result=False,
            etl_page=_etl_page,
            etl_href="etl_mod_post",
            etl_do=getStatus('do'),
            etl_png="../static/etl.jpg",
            etl_info=getStatus('info')
        )
        context.update(setMenus())

        if _etl_page == 1:
            if getStatus('do') == 1:
                template_name = 'etltools/form/register.html'
            else:
                template_name = 'etltools/modlist.html'
                _page, _info = getList(EtlMod)
                context['pagination'] = _page
                context['mods'] = _info

        elif _etl_page == 2:
            if getStatus('do') == 1:
                template_name = 'etltools/form/register.html'
            else:
                template_name = 'etltools/tasklist.html'
                _page, _info = getList(EtlTask)
                context['pagination'] = _page
                context['tasks'] = _info

                context['text'] = _task_log

        elif _etl_page == 3:
            if getStatus('do') == 1:
                template_name = 'etltools/form/register.html'
                context['form'] = JobForm()
            else:
                template_name = 'etltools/joblist.html'
                _page, _info = getList(EtlJob)
                context['pagination'] = _page
                context['jobs'] = _info

                context['text'] = _job_log

        else:
            if getStatus('do') == 1:
                template_name = 'etltools/form/register.html'
            else:
                template_name = 'etltools/dirlist.html'
                _page, _info = getList(EtlDir)
                context['pagination'] = _page
                context['dirs'] = _info

                context['path'] = u'根目录'

        return jsonify(body=render_template(template_name, **context))

class ETLServerDelete(MethodView):
    methods = ['POST']

    def post(self):

        global _etl_page

        _name = request.json.get('server_name')

        context = dict(
            form=setForm(_etl_page),
            result=True,
            etl_page=_etl_page,
            etl_href="etl_mod_post",
            etl_do=getStatus('do'),
            etl_info=getStatus('info')
        )
        context.update(setMenus())

        if _etl_page == 0:
            etl = EtlManager(EtlDir)
        elif _etl_page == 1:
            etl = EtlManager(EtlMod)
        elif _etl_page == 2:
            etl = EtlManager(EtlTask)
            deleteTask(_name)
        elif _etl_page == 3:
            etl = EtlManager(EtlJob)
            deleteJob(_name)

        _str = {'name':_name}
        etl.delete_by(**_str)

        if _etl_page == 0:
            _template_name = 'etltools/dirlist.html'
            _page, _info = getList(EtlDir)
            context['dirs'] = _info
            context['pagination'] = _page
        elif _etl_page == 1:
            _page, _info = getList(EtlMod)
            _template_name = 'etltools/modlist.html'
            context['mods'] = _info
            context['pagination'] = _page
        elif _etl_page == 2:
            _page, _info = getList(EtlTask)
            _template_name = 'etltools/tasklist.html'
            context['tasks'] = _info
            context['pagination'] = _page
        elif _etl_page == 3:
            _page, _info = getList(EtlJob)
            _template_name = 'etltools/joblist.html'
            context['jobs'] = _info
            context['pagination'] = _page

        context['etl_info'] = getStatus('info')

        return jsonify(body=render_template(_template_name, **context))

class ETLTaskRun(MethodView):
    methods = ['POST']

    def post(self):

        global _etl_page, _task_log

        _url = rest_get_url('etl-task/')
        if _url != '':
            _taskname = request.json.get('task-name')
            '''
            2015.8.31 TODO: 目前尚未考虑多台ETL服务器的情况
            _server = request.json.get('server')
            '''
            _mod = request.json.get('mod')

            if _etl_page == 2:
                etl = EtlManager(EtlMod)
                _rec = etl.get(_mod)
                if _rec is not None:
                    _path = '/home/shenwei/nebula/static/etl_mod/'+_rec.filename

                    """ 调用 REST API 激活任务
                        接口参数：
                            {   'src-dir':      模块文件全路径，例如：'/home/shenwei/data/myphone.json.ktr',
                                'task-name':    任务名称，例如'my-tester'}
                    """
                    _api_data = {'src-dir': _path, 'task-name': _taskname, 'cmd': _rec.cmd}
                    restAPI(_url,_api_data)
                    setTaskStatus(_taskname,'1')
                else:
                    setTaskStatus(_taskname,'ERROR')

        context = dict(
            form=setForm(_etl_page),
            result=True,
            etl_page=_etl_page,
            etl_href="etl_mod_post",
            etl_do=getStatus('do'),
            etl_info=getStatus('info')
        )
        context.update(setMenus())

        if _etl_page == 0:
            _page, _info = getList(EtlServer)
            _template_name = 'etltools/dirlist.html'
            context['servers'] = _info
        elif _etl_page == 1:
            _page, _info = getList(EtlMod)
            _template_name = 'etltools/modlist.html'
            context['mods'] = _info
        elif _etl_page == 2:
            _page, _info = getList(EtlTask)
            _template_name = 'etltools/tasklist.html'
            context['tasks'] = _info
            _task_log = []
            context['text'] = _task_log
        elif _etl_page == 3:
            _page, _info = getList(EtlJob)
            _template_name = 'etltools/joblist.html'
            context['jobs'] = _info

        context['pagination'] = _page
        context['etl_info'] = getStatus('info')

        return jsonify(body=render_template(_template_name, **context))

class ETLTaskLog(MethodView):
    methods = ['POST']

    def post(self):

        global _etl_page, _task_log

        _name = request.json.get('task_name')

        context = dict(
            form=setForm(_etl_page),
            result=True,
            etl_page=_etl_page,
            etl_href="etl_mod_post",
            etl_do=getStatus('do'),
            etl_info=getStatus('info')
        )
        context.update(setMenus())

        _page, _info = getList(EtlTask)
        _template_name = 'etltools/text.html'
        context['tasks'] = _info
        context['pagination'] = _page
        context['etl_info'] = getStatus('info')

        """ 获取 ETL任务 的日志
        """
        _url = rest_get_url('etl-task-log/')
        _task_log = rest_get_task_log(_url, _name)['text']
        context['text'] = _task_log

        return jsonify(body=render_template(_template_name, **context))

def validSchedule(schedule):
    """
    判断 调度策略 格式是否正确

    :param schedule: 调度策略
    :return: 正确:True, 错误:False
    """

    _key = [{'min':0,'max':59},{'min':0,'max':59},{'min':1,'max':31},{'min':1,'max':12},{'min':0,'max':6}]
    _entrys = schedule.split(' ')
    if len(_entrys)<5:
        return False
    """
    2015.12.10 by shenwei.
    if _entrys[0]=="*" and _entrys[1]=="*" and _entrys[2]=="*" and _entrys[3]=="*" and _entrys[4]=="*":
        return False
    """

    for _i in range(0,5):
        if _entrys[_i].isdigit():
            if (int(_entrys[_i]) < _key[_i]['min']) or (int(_entrys[_i]) >_key[_i]['max']):
                return False
        elif _entrys[_i] != "*" and _entrys[_i][0] != '%':
            return False

    return True

class ETLJobRun(MethodView):
    methods = ['POST']

    def post(self):

        global _etl_page, _job_log

        _url = rest_get_url('etl-job/')
        if _url != '':
            _jobname = request.json.get('task-name')
            _schedule = request.json.get('schedule')
            '''
            2015.8.31 TODO: 目前尚未考虑多台ETL服务器的情况
            _server = request.json.get('server')
            '''
            _mod = request.json.get('mod')

            if validSchedule(_schedule):
                if _etl_page == 3:
                    etl = EtlManager(EtlMod)
                    _rec = etl.get(_mod)
                    if _rec is not None:
                        _path = '/home/shenwei/nebula/static/etl_mod/'+_rec.filename

                        """ 调用 REST API 激活任务
                            接口参数：
                                {   'src-dir':      模块文件全路径，例如：'/home/shenwei/data/myphone.json.ktr',
                                    'task-name':    任务名称，例如'my-tester'}
                        """
                        _api_data = {'src-dir': _path, 'job-name': _jobname, 'scheduler': _schedule, 'cmd': _rec.cmd}
                        restAPI(_url,_api_data)
                        setJobStatus(_jobname,'1')
                    else:
                        setJobStatus(_jobname,'ERROR')
            else:
                setJobStatus(_jobname,'ERROR')

        context = dict(
            form=setForm(_etl_page),
            result=True,
            etl_page=_etl_page,
            etl_href="etl_mod_post",
            etl_do=getStatus('do'),
            etl_info=getStatus('info')
        )
        context.update(setMenus())

        if _etl_page == 0:
            _page, _info = getList(EtlDir)
            _template_name = 'etltools/dirlist.html'
            context['servers'] = _info
        elif _etl_page == 1:
            _page, _info = getList(EtlMod)
            _template_name = 'etltools/modlist.html'
            context['tasks'] = _info
        elif _etl_page == 2:
            _page, _info = getList(EtlTask)
            _template_name = 'etltools/tasklist.html'
            context['tasks'] = _info
        else:
            _etl_page = 3
            _page, _info = getList(EtlJob)
            _template_name = 'etltools/joblist.html'
            context['jobs'] = _info
            _job_log = []
            context['text'] = _job_log

        context['pagination'] = _page
        context['etl_info'] = getStatus('info')

        return jsonify(body=render_template(_template_name, **context))

class ETLJobLog(MethodView):
    methods = ['POST']

    def post(self):

        global _etl_page, _job_log

        _name = request.json.get('job_name')

        context = dict(
            form=setForm(_etl_page),
            result=True,
            etl_page=_etl_page,
            etl_href="etl_mod_post",
            etl_do=getStatus('do'),
            etl_info=getStatus('info')
        )
        context.update(setMenus())

        _page, _info = getList(EtlTask)
        _template_name = 'etltools/text.html'
        context['tasks'] = _info
        context['pagination'] = _page
        context['etl_info'] = getStatus('info')

        """ 获取 ETL任务 的日志
        """
        _url = rest_get_url('etl-job-log/')
        _job_log = rest_get_job_log(_url, _name)['text']
        context['text'] = _job_log

        return jsonify(body=render_template(_template_name, **context))

def restAPI(url,api_data):
    """
    调用 REST 服务
    :param api_data:
    :return:
    """
    _data_urlencode = urllib.urlencode(api_data)
    _req = urllib2.Request(url=url, data=_data_urlencode)
    _res_data = urllib2.urlopen(_req)
    _res = _res_data.read()
    return _res

def deleteTask(taskname):

    _url = rest_get_url('etl-task-delete/')
    if _url is not "":
        _api_data = {'task-name': taskname}
        restAPI(_url,_api_data)

def deleteJob(jobname):

    _url = rest_get_url('etl-job-delete/')
    if _url is not "":
        _api_data = {'job-name': jobname}
        restAPI(_url,_api_data)


