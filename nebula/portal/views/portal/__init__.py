# -*- coding: utf-8  -*-

from flask import Blueprint

from nebula.core.i18n import _

from .dashboard import DashboardView
from .home import HomeView
from .users import LoginView
from .users import LogoutView

portal_bp = Blueprint('portal',
                      __name__,
                      static_folder='static',
                      static_url_path='/static')

# Home/Dashboard page
portal_bp.add_url_rule('/',
                       view_func=HomeView.as_view('home'))

# 2015-10-22 by shenwei
# for nebula-mini
#
# portal_bp.add_url_rule('/dashboard',
#                       view_func=DashboardView.as_view('dashboard'))
#

portal_bp.add_url_rule('/login',
                       view_func=LoginView.as_view('login'))

portal_bp.add_url_rule('/logout',
                       view_func=LogoutView.as_view('logout'))

from .datamng import (
    DataMngView,
    DataElementDelete,
    DataMngChange,
    DataMngReport,
    ShowProductInfo,
    ShowProjectInfo,
)

portal_bp.add_url_rule('/datamng/',
                       view_func=DataMngView.as_view('datamng'),
                       methods=['POST', 'GET'])

portal_bp.add_url_rule('/datamng/datamngchange',
                       view_func=DataMngChange.as_view('datamngchange'),
                       methods=['POST', 'GET'])

portal_bp.add_url_rule('/datamng/datamngreport',
                       view_func=DataMngReport.as_view('datamngreport'),
                       methods=['POST'])

portal_bp.add_url_rule('/datamng/dataelementdelete',
                       view_func=DataElementDelete.as_view('dataelementdelete'),
                       methods=['POST'])

portal_bp.add_url_rule('/datamng/showproductinfo',
                       view_func=ShowProductInfo.as_view('showproductinfo'),
                       methods=['POST'])

portal_bp.add_url_rule('/datamng/showprojectinfo',
                       view_func=ShowProjectInfo.as_view('showprojectinfo'),
                       methods=['POST'])

from .hadoop import (
    CDHListView,
    CDHChange,
    CDHReport,
)

portal_bp.add_url_rule('/cdh/',
                       view_func=CDHListView.as_view('cdh'),
                       methods=['POST', 'GET'])

portal_bp.add_url_rule('/cdh/datainchange',
                       view_func=CDHChange.as_view('datainchange'),
                       methods=['POST', 'GET'])

portal_bp.add_url_rule('/cdh/datainreport',
                       view_func=CDHReport.as_view('datainreport'),
                       methods=['POST'])

from .empty import (
    EMPTYView
)

portal_bp.add_url_rule('/empty',
                       view_func=EMPTYView.as_view('empty'),
                       methods=['GET'],
                       defaults={'view_desc': _(u"Empty - Going...")})

from .etltools import (
    ETLToolsView,
    ETLChange,
    ETLReport,
    ETLServerDelete,
    ETLToolsGetPage,
    ETLTaskRun,
    ETLJobRun,
    ETLTaskLog,
    ETLJobLog,
)

portal_bp.add_url_rule('/etltools',
                       view_func=ETLToolsView.as_view('etltools'),
                       methods=['GET', 'POST'])

portal_bp.add_url_rule('/etltools/change',
                       view_func=ETLChange.as_view('change'),
                       methods=['POST', 'GET'])

portal_bp.add_url_rule('/etltools/report',
                       view_func=ETLReport.as_view('report'),
                       methods=['POST'])

portal_bp.add_url_rule('/etltools/getpage',
                       view_func=ETLToolsGetPage.as_view('getpage'),
                       methods=['GET'])

portal_bp.add_url_rule('/etltools/serverdelete',
                       view_func=ETLServerDelete.as_view('serverdelete'),
                       methods=['POST'])

portal_bp.add_url_rule('/etltools/etltaskrun',
                       view_func=ETLTaskRun.as_view('etltaskrun'),
                       methods=['POST'])

portal_bp.add_url_rule('/etltools/etljobrun',
                       view_func=ETLJobRun.as_view('etljobrun'),
                       methods=['POST'])

portal_bp.add_url_rule('/etltools/gettasklog',
                       view_func=ETLTaskLog.as_view('gettasklog'),
                       methods=['POST'])

portal_bp.add_url_rule('/etltools/getjoblog',
                       view_func=ETLJobLog.as_view('getjoblog'),
                       methods=['POST'])

from .webapp import (
    MUSICView
)

portal_bp.add_url_rule('/music/music',
                       view_func=MUSICView.as_view('music'),
                       methods=['GET','POST'])
