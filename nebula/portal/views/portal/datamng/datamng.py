# -*- coding: utf-8 -*-
"""
"""

__author__ = 'shenwei'

from nebula.core.views import TemplateView
import os,sys
import logging
import urllib
import urllib2
import json
import types

"""设置字符集
"""
reload(sys)
sys.setdefaultencoding('utf-8')

from nebula.core.managers.datamngmod import DataManager
from nebula.core.models.datamngmod import DataElement

from nebula.core.managers.upfilemod import UpFileManager
from nebula.core.models.upfilemod import UpFileMod

from nebula.core.managers.membermod import MemberManager
from nebula.core.models.membermod import MemberMod

from nebula.core.managers.projectmod import ProjectManager
from nebula.core.models.projectmod import ProjectMod

from nebula.core.managers.productmod import ProductManager
from nebula.core.models.productmod import ProductMod

from nebula.core.managers.taskmod import TaskManager
from nebula.core.models.taskmod import TaskMod

from nebula.core.managers.enginerringmod import EnginerringManager
from nebula.core.models.enginerringmod import EnginerringMod

from nebula.core.managers.deliverymod import DeliveryManager
from nebula.core.models.deliverymod import DeliveryMod

from flask.ext.paginate import Pagination
from nebula.portal.utils.menu import setMenus


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

_page_idx = []
_page = 0

MAX_ENTRY = 8
N_PAGE = 20
for i in range(0, MAX_ENTRY):
    _page_idx.append(1)

def getList(model):
    """
    获取数据模型的列表

    :param model:
    :return:
    """

    global _page_idx, _page, N_PAGE

    if model == DataElement:
        model_name = u'数据元管理'
    elif model == MemberMod:
        model_name = u'员工列表'
    elif model == ProjectMod:
        model_name = u'项目列表'
    elif model == ProductMod:
        model_name = u'产品列表'
    elif model == TaskMod:
        model_name = u'任务列表'
    elif model == EnginerringMod:
        model_name = u'工程列表'
    elif model == DeliveryMod:
        model_name = u'产品交付列表'
    elif model == UpFileMod:
        model_name = u'文件上传日志'
    _rec = getAll(model)

    page = _page_idx[_page]

    _index = (page-1) * N_PAGE
    _next = _index + N_PAGE
    if _next > len(_rec):
        """ 2015.9.15 by shenwei @chengdu
            当本页面内容被删完时，应转到上一页
        """
        if len(_rec[_index:])==0 and page>1:
            page -= 1
            _page_idx[_page] = page
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

    if model == DataElement:
        dataMng = DataManager(model)
    elif model == MemberMod:
        dataMng = MemberManager(MemberMod)
    elif model == ProjectMod:
        dataMng = ProjectManager(ProjectMod)
    elif model == ProductMod:
        dataMng = ProductManager(ProductMod)
    elif model == TaskMod:
        dataMng = TaskManager(TaskMod)
    elif model == EnginerringMod:
        dataMng = EnginerringManager(EnginerringMod)
    elif model == DeliveryMod:
        dataMng = DeliveryManager(DeliveryMod)
    elif model == UpFileMod:
        dataMng = UpFileManager(UpFileMod)
    _recs = dataMng.list()

    if _recs == None:
        return None

    _posts = []

    for _rec in _recs:
        _post = {}
        if model == DataElement:
            _post['name'] = _rec.keyid
            _post['keyid'] = _rec.keyid
            _post['val'] = _rec.val
            _post['val_desc'] = _rec.val_desc
            _post['val_type'] = _rec.val_type
            _post['created_at'] = _rec.created_at
        elif model == MemberMod:
            _post['name'] = _rec.MM_XM
            _post['id'] = _rec.id
            _post['number'] = _rec.MM_GH
            _post['state'] = _rec.MM_ZT
            _post['updated_at'] = _rec.updated_at
        elif model == ProjectMod:
            _post['PJ_XMMC'] = _rec.PJ_XMMC
            _post['PJ_XMBH'] = _rec.PJ_XMBH
            _post['PJ_XMFZR'] = _rec.PJ_XMFZR
            _post['PJ_LXSJ'] = _rec.PJ_LXSJ
            _post['PJ_KSSJ'] = _rec.PJ_KSSJ
            _post['PJ_JSSJ'] = _rec.PJ_JSSJ
            _post['PJ_XMJJ'] = _rec.PJ_XMJJ
            _post['PJ_XMYS'] = _rec.PJ_XMYS
            _post['PJ_XMZT'] = _rec.PJ_XMZT
            _post['PJ_XMXZ'] = _rec.PJ_XMXZ
            _post['PJ_JFSJ'] = _rec.PJ_JFSJ
            _post['PJ_SJFY'] = _rec.PJ_SJFY
            _post['PJ_MBYH'] = _rec.PJ_MBYH
            _post['BgEdDate'] = _rec.PJ_KSSJ+u'至'+_rec.PJ_JSSJ
        elif model == ProductMod:
            _post['PD_MC'] = _rec.PD_MC
            _post['PD_DH'] = _rec.PD_DH
            _post['PD_LX'] = _rec.PD_LX
            _post['PD_BBH'] = _rec.PD_BBH
            _post['PD_FBSJ'] = _rec.PD_FBSJ
        elif model == TaskMod:
            _post['TK_RW'] = _rec.TK_RW
            _post['TK_XMBH'] = _rec.TK_XMBH
            _post['TK_RWNR'] = _rec.TK_RWNR
            _post['TK_ZXDZ'] = _rec.TK_ZXDZ
            _post['TK_KSSJ'] = _rec.TK_KSSJ
            _post['TK_JSSJ'] = _rec.TK_JSSJ
            _post['TK_ZXR'] = _rec.TK_ZXR
            _post['TK_BZ'] = _rec.TK_BZ
            _post['TK_SQR'] = _rec.TK_SQR
            _post['TK_RWZT'] = _rec.TK_RWZT
            _post['TK_GZSJ'] = _rec.TK_GZSJ
            _kssj = _rec.TK_KSSJ
            if type(_rec.TK_KSSJ) is types.NoneType:
                _kssj = '-'
            _jssj = _rec.TK_JSSJ
            if type(_rec.TK_JSSJ) is types.NoneType:
                _jssj = '-'
            _post['BgEdDate'] = _kssj + u'至' + _jssj
        elif model == EnginerringMod:
            _post['EG_NAME'] = _rec.EG_NAME
            _post['EG_BH'] = _rec.EG_BH
            _post['EG_STATE'] = _rec.EG_STATE
            _post['EG_PJ_BH'] = _rec.EG_PJ_BH
            _post['EG_SITE'] = _rec.EG_SITE
            _post['EG_ENV'] = _rec.EG_ENV
        elif model == DeliveryMod:
            _post['EG_BH'] = _rec.EG_BH
            _post['PD_DH'] = _rec.PD_DH
            _post['PD_VERSION'] = _rec.PD_VERSION
            _post['DL_DATE'] = _rec.DL_DATE
            _post['DL_STATE'] = _rec.DL_STATE
        elif model == UpFileMod:
            _post['name'] = _rec.id
            _post['id'] = _rec.id
            _post['filename'] = _rec.filename
            _post['desc'] = _rec.desc
            _post['version'] = _rec.version
            _post['created_at'] = _rec.created_at
        _posts.append(_post)
    return _posts

class DataMngView(MethodView):
    """
    GET请求：获取页面内容
    POST请求：提交页面记录
    """

    methods = ['GET', 'POST']

    _template_name = 'datamng/datamngbase.html'

    def get(self):

        global _page

        try:
            _page_idx[_page] = int(request.args.get('page', 1))
        except ValueError:
            _page_idx[_page] = 1
        finally:

            context = dict(
                result=False,
                _page=_page,
                etl_href="etl_mod_post",
                etl_body=True,
                etl_png="../static/etl.jpg",
            )
            context.update(setMenus())

            """ 获取UI的当前页面，并获取该页面对应数据模型的记录数据（供列表显示）
            """
            __page = request.args.get('etl_app')
            if __page == 'data_element_list':
                _page = 0
                _resp_page, _info = getList(DataElement)
                context['pagination'] = _resp_page
                context['dirs'] = _info
            elif __page == 'member_list':
                _page = 0
                _resp_page, _info = getList(MemberMod)
                context['pagination'] = _resp_page
                context['dirs'] = _info
            elif __page == 'project_list':
                _page = 0
                _resp_page, _info = getList(ProductManager)
                context['pagination'] = _resp_page
                context['dirs'] = _info
            elif __page == 'product_list':
                _page = 0
                _resp_page, _info = getList(ProductMod)
                context['pagination'] = _resp_page
                context['dirs'] = _info
            elif __page == 'task_list':
                _page = 0
                _resp_page, _info = getList(TaskMod)
                context['pagination'] = _resp_page
                context['dirs'] = _info
            elif __page == 'enginerring_list':
                _page = 0
                _resp_page, _info = getList(EnginerringMod)
                context['pagination'] = _resp_page
                context['dirs'] = _info
            elif __page == 'delivery_list':
                _page = 0
                _resp_page, _info = getList(DeliveryMod)
                context['pagination'] = _resp_page
                context['dirs'] = _info
            elif __page == 'upfile_list':
                _page = 0
                _resp_page, _info = getList(UpFileMod)
                context['pagination'] = _resp_page
                context['dirs'] = _info
            else:
                _page = 0
                _resp_page, _info = getList(DataElement)
                context['pagination'] = _resp_page
                context['dirs'] = _info

            context['_page'] = _page

            return render_template(self._template_name, **context)

class DataMngReport(MethodView):
    """
    2015.7.29 shenwei @chengdu
    这是一个处理 jQuery 请求的服务
    """

    methods = ['POST']

    _template_name = 'datamng/datamngbase.html'

    def post(self):

        global _page

        _page = int(request.json.get('value'))

        form = setForm(_page)

        context = dict(
            result=False,
            form=form,
            _page=_page,
            etl_href="etl_mod_post",
            etl_png="../static/etl.jpg",
        )
        context.update(setMenus())

        return jsonify(body=render_template(self._template_name, **context))

class DataMngChange(MethodView):

    methods = ['POST', 'GET']

    def get(self):
        """
        用于 列表翻页 的刷新

        :return:
        """
        global _page_idx, _page

        try:
            _page_idx[_page] = int(request.args.get('page', 1))
        except ValueError:
            _page_idx[_page] = 1
        finally:

            context = dict(
                result=False,
                _page=_page,
                etl_href="etl_mod_post",
                etl_png="../static/etl.jpg",
            )
            context.update(setMenus())

            if _page == 0:
                _resp_page, _info = getList(DataElement)
                template_name = 'datamng/dataelementlist.html'
            elif _page == 1:
                _resp_page, _info = getList(MemberMod)
                template_name = 'datamng/memberlist.html'
            elif _page == 2:
                _resp_page, _info = getList(ProjectMod)
                template_name = 'datamng/projectlist.html'
            elif _page == 3:
                _resp_page, _info = getList(TaskMod)
                template_name = 'datamng/tasklist.html'
            elif _page == 4:
                _resp_page, _info = getList(ProductMod)
                template_name = 'datamng/productlist.html'
            elif _page == 5:
                _resp_page, _info = getList(EnginerringMod)
                template_name = 'datamng/enginerringlist.html'
            elif _page == 6:
                _resp_page, _info = getList(DeliveryMod)
                template_name = 'datamng/deliverylist.html'
            elif _page == 7:
                _resp_page, _info = getList(UpFileMod)
                template_name = 'datamng/upfilelist.html'

            context['pagination'] = _resp_page
            context['dirs'] = _info

            return render_template('datamng/datamngbase.html', **context)
            #return jsonify(body=render_template(template_name, **context))

    def post(self):
        """
        请求来自于：页面切换

        :return:
        """

        global _page

        _value = int(request.json.get('value'))
        if _value <= 7:
            _page = _value

        context = dict(
            result=False,
            _page=_page,
            etl_href="etl_mod_post",
            etl_png="../static/etl.jpg",
        )
        context.update(setMenus())
        if _value==0:
            _resp_page, _info = getList(DataElement)
            template_name = 'datamng/dataelementlist.html'
        elif _value==1:
            _resp_page, _info = getList(MemberMod)
            template_name = 'datamng/memberlist.html'
        elif _value==2:
            _resp_page, _info = getList(ProjectMod)
            template_name = 'datamng/projectlist.html'
        elif _value==3:
            _resp_page, _info = getList(TaskMod)
            template_name = 'datamng/tasklist.html'
        elif _value==4:
            _resp_page, _info = getList(ProductMod)
            template_name = 'datamng/productlist.html'
        elif _value == 5:
            _resp_page, _info = getList(EnginerringMod)
            template_name = 'datamng/enginerringlist.html'
        elif _value == 6:
            _resp_page, _info = getList(DeliveryMod)
            template_name = 'datamng/deliverylist.html'
        elif _value == 7:
            _resp_page, _info = getList(UpFileMod)
            template_name = 'datamng/upfilelist.html'
        context['dirs'] = _info
        context['pagination'] = _resp_page

        return jsonify(body=render_template(template_name, **context))

class DataElementDelete(MethodView):
    methods = ['POST']

    def post(self):

        global _page

        _name = request.json.get('keyid')

        context = dict(
            result=True,
            _page=_page,
            etl_href="etl_mod_post",
        )
        context.update(setMenus())

        etl = DataManager(DataElement)
        _str = {'keyid':_name}
        etl.delete_by(**_str)

        _template_name = 'datamng/dataelementlist.html'
        _resp_page, _info = getList(DataElement)
        context['dirs'] = _info
        context['pagination'] = _resp_page

        return jsonify(body=render_template(_template_name, **context))

import MySQLdb

class ShowProductInfo(MethodView):
    methods = ['POST']

    def post(self):

        global _page

        db = MySQLdb.connect("localhost","root","mysqlroot","nebula",charset="utf8")
        _name = request.json.get('name')
        _name = _name.split(':')
        _pd_dh = _name[0]
        _pd_bbh = _name[1]

        _sql = "SELECT title,requirment FROM requirment_t WHERE PD_BH='%s' and PD_BBH='%s'" % (_pd_dh,_pd_bbh)
        _cur = db.cursor()
        _cur.execute(_sql)
        _res = _cur.fetchall()

        db.close()

        _s = []
        _s.append(u"产品：" + _pd_dh)
        _s.append(u"版本：" + _pd_bbh)
        _s.append("=" * len(_s[0]))

        _i = 1
        for _row in _res:
            __s = u"第%d条：" % _i
            _s.append(__s)
            __s = u"..【功能】%s" % _row[0]
            _s.append(__s)
            __s = u"..【描述】%s" % _row[1]
            _s.append(__s)
            _s.append("-------------")
            _i = _i + 1

        context = dict(
            result=True,
            _page=_page,
            etl_href="etl_mod_post",
            _info="'功能列表：'",
        )

        _template_name = 'datamng/text.html'

        """ 获取 ETL任务 的日志
        """
        context['text'] = _s

        return jsonify(body=render_template(_template_name, **context))

class ShowProjectInfo(MethodView):
    methods = ['POST']

    def post(self):

        global _page

        db = MySQLdb.connect("localhost","root","mysqlroot","nebula",charset="utf8")
        _name = request.json.get('name')

        _s = []
        _s.append(u"项目：" + _name)
        _s.append("=" * len(_s[0]))

        _sql = "SELECT EG_SITE,EG_STATE FROM enginerring_t WHERE EG_PJ_BH='%s' " % _name
        _cur = db.cursor()
        _cur.execute(_sql)
        _row = _cur.fetchone()

        if _row is not None and len(_row)>0:
            __s = u"【场地】%s" % _row[0]
            _s.append(__s)
            __s = u"【状态】%s" % _row[1]
            _s.append(__s)
            _s.append("=" * len(_s[3]))

        _sql = "SELECT PD_DH,PD_VERSION,DL_DATE,DL_STATE FROM delivery_t WHERE EG_BH='%s' " % _name
        _cur = db.cursor()
        _cur.execute(_sql)
        _res = _cur.fetchall()

        for _row in _res:
            __s = u"【产品】%s 【版本】%s" % (_row[0],_row[1])
            _s.append(__s)
            __s = u"..【交付日期】%s" % _row[2]
            _s.append(__s)
            __s = u"..【交付状态】%s" % _row[3]
            _s.append(__s)
            _s.append("--------")

        db.close()

        context = dict(
            result=True,
            _page=_page,
            _info="'工程信息：'",
            etl_href="etl_mod_post",
        )

        _template_name = 'datamng/text.html'

        """ 获取 ETL任务 的日志
        """
        context['text'] = _s

        return jsonify(body=render_template(_template_name, **context))

