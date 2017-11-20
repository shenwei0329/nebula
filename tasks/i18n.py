# -*- coding: utf-8 -*-
from invoke import task, run

from nebula.core import constants


@task
def extract_messages():
    """
    抽取pot文件
    :return:
    """
    run('pybabel extract -F babel.cfg -o {locale_path}/messages.pot .'.format(
        locale_path=constants.RELATIVE_LOCALE_PATH
    ), echo=True)


@task
def init_catalog(language=None):
    """
    初始化locale目录
    :return:
    """
    run('pybabel init -i {locale_path}/messages.pot -d {locale_path} -l {language}'.format(
        locale_path=constants.RELATIVE_LOCALE_PATH, language=language or constants.DEFAULT_LOCALE
    ), echo=True)


@task
def update_catalog():
    """
    更新locale目录po文件
    :return:
    """
    run('pybabel update -i {locale_path}/messages.pot -d {locale_path}'.format(
        locale_path=constants.RELATIVE_LOCALE_PATH
    ), echo=True)


@task
def compile_catalog():
    """
    从po文件编译mo文件
    :return:
    """
    run('pybabel compile -d {locale_path}'.format(locale_path=constants.RELATIVE_LOCALE_PATH))
    run('pybabel compile -d {locale_path} -D wtforms'.format(locale_path=constants.RELATIVE_LOCALE_PATH))


@task(default=True)
def refresh_catalog():
    """
    i18n集成命令, 抽取 > 更新po文件 > 生成mo文件
    :return:
    """
    extract_messages()
    update_catalog()
    compile_catalog()
