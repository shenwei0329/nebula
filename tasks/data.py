# -*- coding: utf-8 -*-

from invoke import task
from nebula.core.managers.etlmod import EtlManager
from nebula.core.models.etlmod import EtlDir, EtlServer, EtlMod, EtlTask, EtlJob
from nebula.core.managers.datamngmod import DataManager
from nebula.core.models.datamngmod import DataElement

@task
def init_etl_model():

    etl = EtlManager(EtlDir)
    param = {
            'desc': u'用于管理ETL脚本文件。',
            }
    etl.create('ETL脚本', **param)
    param = {
            'desc': u'用于管理Spark运行文件。',
            }
    etl.create('Spark脚本', **param)

@task
def init():
    """
    初始化数据库：预置数据库记录
    :return:
    """
    init_etl_model()