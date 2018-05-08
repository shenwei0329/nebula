#encoding:utf-8
import os
PATH = os.path.dirname(os.path.abspath(__file__))
os.sys.path.append(os.path.dirname(PATH))
from sqlalchemy import func
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from nebula.core import (
    Instance,
    Volume,
    Virtualrouter,
    SecurityGroup,
    Network,
    User)
from oslo.config import cfg
from nebula.core.models import Quota

CONF = cfg.CONF
CONF.import_group('portal', 'nebula.core.db.options')


def create_engine(connection_uri, **kwargs):
    engine = sqlalchemy.create_engine(connection_uri, **kwargs)
    return engine


def get_session():
    from nebula.core import config
    config.set_defaults(args=[], prog='blah')
    engine = create_engine(cfg.CONF.database.connection)
    session_maker = sessionmaker(bind=engine)
    return session_maker()


if __name__ == '__main__':
    quotas = dict()
    session = get_session()

    for q in session.query(
        Quota.user_id,
        Quota.resource,
        Quota.hard_limit,
        User.username
    ).outerjoin(User, User.id == Quota.user_id).all():
        if q[0] in quotas:
            quotas[q[0]][q[1]] = dict(
                quota=q[2],
                in_use=None,
                verbose=u""
            )
        else:
            quotas[q[0]] = dict()
            quotas[q[0]]["username"] = q[3]
            quotas[q[0]][q[1]] = dict(
                quota=q[2],
                in_use=None,
                verbose=u""
            )

    instance_quota = session.query(
        User.id,
        User.username,
        func.count('1'),
        func.sum(Instance.vcpus),
        func.sum(Instance.memory_mb)).join(Instance.owner).group_by(User.username).all()

    for ins in instance_quota:
        if not ins or len(ins) != 5:
            continue
        quotas[ins[0]]["instances"]["in_use"] = ins[2]
        quotas[ins[0]]["instances"]["verbose"] = u"虚拟机"
        quotas[ins[0]]["cores"]["in_use"] = int(ins[3])
        quotas[ins[0]]["cores"]["verbose"] = u"Vcpu"
        quotas[ins[0]]["ram"]["in_use"] = int(ins[4])
        quotas[ins[0]]["ram"]["verbose"] = u"内存"

    volume_quota = session.query(
        User.id,
        User.username,
        func.sum(Volume.size)
    ).join(Volume.owner).group_by(User.username).all()

    for v in volume_quota:
        if not v or len(v) != 3:
            continue
        quotas[v[0]]["volumes"]["in_use"] = int(v[2])
        quotas[v[0]]["volumes"]["verbose"] = u"磁盘容量"

    network_quota = session.query(
        User.id,
        User.username,
        func.count('1')
    ).join(Network.owner).group_by(User.username).all()

    for n in network_quota:
        if not v or len(v) != 3:
            continue
        quotas[n[0]]["private_networks"]["in_use"] = int(n[2])
        quotas[n[0]]["private_networks"]["verbose"] = u"私有网络"

    security_group_quota = session.query(
        User.id,
        User.username,
        func.count('1')
    ).join(SecurityGroup.owner).group_by(User.username).all()

    for n in security_group_quota:
        if not v or len(v) != 3:
            continue
        quotas[n[0]]["firewalls"]["in_use"] = int(n[2])
        quotas[n[0]]["firewalls"]["verbose"] = u"虚拟防火墙"

    virtualrouter_quota = session.query(
        User.id,
        User.username,
        func.count('1'),
        func.sum(Virtualrouter.bandwidth_tx),
        func.sum(Virtualrouter.bandwidth_rx)
    ).join(Virtualrouter.owner).group_by(User.username).all()

    for item in virtualrouter_quota:
        if not item or len(item) != 5:
            continue
        quotas[item[0]]["virtual_routers"]["in_use"] = item[2]
        quotas[item[0]]["virtual_routers"]["verbose"] = u"虚拟路由器"
        quotas[item[0]]["bandwidth_tx"]["in_use"] = int(item[3])
        quotas[item[0]]["bandwidth_tx"]["verbose"] = u"上行带宽"
        quotas[item[0]]["bandwidth_rx"]["in_use"] = int(item[4])
        quotas[item[0]]["bandwidth_rx"]["verbose"] = u"下行带宽"

    print u"*******************同步配额信息*******************\n"
    for i, value in quotas.items():
        print u"用户登录名：[%s]\t用户ID：[%s]\n" % (value["username"], i)
        for k, v in value.items():
            if k == "username" or not v["in_use"]:
                continue
            print u"\t\t[%s]\t数据库字段：[%s]\t总配额：[%s]\t已用配额：[%s]" % (v["verbose"], k, v["quota"], v["in_use"])