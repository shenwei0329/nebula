# -*- coding: utf-8 -*-
from __future__ import print_function
from invoke import task

from nebula.core.managers import base as base_manager
from nebula.core.managers import managers
from nebula.core.db.session import get_engine
from oslo_config import cfg

CONF = cfg.CONF
CONF.import_group('portal', 'nebula.portal.options')

"""
    type                enum          meter类型 1表示主机；2表示虚拟机
    meter_name          varchar(32)   显示名称
    meter_value         varchar(32)   值
    unit                varchar(32)   单位
    min_value           int           可设置的最小值
    max_value           int           可设置的最大值
    state               bool          可用状态
    description         text          描述
    create_at           datetime      创建时间
    update_at           varchar(39)   更新时间
    """

DEFAULT_ALARM_METERS = [{"type": 1, "meter_name": "cpu使用率", "meter_value": "compute.node.cpu.percent",
                         "unit": "%", "min_value": 50, "max_value": 100, "description":"主机cpu使用率"},

                        {"type": 1, "meter_name": "内存使用率", "meter_value": "compute.node.mem.usage",
                         "unit": "%", "min_value": 50, "max_value": 100, "description":"主机内存使用率"},

                        {"type": 1, "meter_name": "磁盘使用率", "meter_value": "compute.node.disk.usage",
                         "unit": "%", "min_value": 50, "max_value": 100, "description":"主机磁盘使用率"},

                        {"type": 2, "meter_name": "cpu使用率",  "meter_value": "cpu_util",
                         "unit": "%", "min_value": 50, "max_value": 100, "description":"虚拟机cpu使用率"},

                        {"type": 2, "meter_name": "内存使用率", "meter_value": "memory.usage",
                         "unit": "%", "min_value": 50, "max_value": 100, "description":"虚拟机内存使用率"},
                        ]


@task
def create():
    base_manager.configure_db()


@task
def drop():
    base_manager.clear_db()


@task
def clean():
    """
     v1.0.5　（11.30版本） 增加７个表
        alarms
        alarm_bindings
        alarm_rules
        alarm_meters　（**此表是默认配置数据，暂时未开启添加功能）
        alarm_time_constraints
        virtualrouter_floatingips
        virtualrouter_subnets
    :return:
    """
    engine = get_engine()
    engine.execute("""
    /* 清除Nebula数据库脚本, 清除资源管理表外所有数据  */
    set foreign_key_checks=0; -- 设置外键失效

    truncate table aggregates;
    truncate table alerts;
    truncate table alarms;
    truncate table alarm_bindings;
    truncate table alarm_rules;
    truncate table alarm_meters;
    truncate table alarm_time_constraints;
    truncate table compute_nodes;
    truncate table flavors;
    truncate table flowdetails;
    truncate table images;
    truncate table instances;
    truncate table instance_backups;
    truncate table jobs;
    truncate table lb_members;
    truncate table lb_pools;
    truncate table lb_pool_statistics;
    truncate table lb_vips;
    truncate table logbooks;
    truncate table networks;
    truncate table permissions;
    truncate table ports;
    truncate table quotas;
    truncate table quota_classes;
    truncate table quota_usages;
    truncate table reservations;
    truncate table roles;
    truncate table role_permissions;
    truncate table security_groups;
    truncate table security_group_ports;
    truncate table security_group_rules;
    truncate table subnets;
    truncate table system_properties;
    delete from users where id <> 1;
    truncate table user_login;
    truncate table user_properties;
    truncate table user_roles;
    truncate table virtualrouters;
    truncate table virtualrouter_nats;
    truncate table virtualrouter_networks;
    truncate table virtualrouter_publicips;
    truncate table virtualrouter_floatingips;
    truncate table virtualrouter_subnets;
    truncate table volumes;
    truncate table volume_backups;

    set foreign_key_checks=1; -- 恢复外键
    """)


@task
def dump():
    print(base_manager.dump_tables())


@task
def create_user():
    managers.users.create('root', 'root', True, CONF.portal.REGION_NAME)

@task
def set_default_alarm_meter():
    """
    告警项初始化
    :return:
    """
    for meter in DEFAULT_ALARM_METERS:
        managers.alarm_meters.create(**meter)


@task
def create_permission(name, view, method):
    managers.permission.create(name, view, method)


@task
def change_password(username, password):
    user = managers.users.get_by_username(username)
    if user is None:
        return
    user_id = user.id

    managers.users.change_password(user_id, password)



# @task
# def create_test_demo():
#     VirtualrouterManager().fixed()
