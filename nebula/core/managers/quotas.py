# -*- coding: utf-8 -*-

import uuid
import logging

from sqlalchemy.sql import func

from nebula.openstack.common import timeutils
from nebula.core.db import session as db_session

from nebula.core.models import Quota
from nebula.core.models import QuotaClass
from nebula.core.models import Reservation
from nebula.core.models import QuotaUsage
from nebula.core.models import Instance
from nebula.core.models import Virtualrouter
from nebula.core.models import Network
from nebula.core.models import VirtualrouterPublicIP
from nebula.core.models import Volume
from nebula.core.models import Image
from nebula.core.models import SecurityGroup

from .base import BaseManager

LOG = logging.getLogger(__name__)

PER_QUOTAS = [
    'instances',
    'virtual_routers',
]


class QuotaManager(BaseManager):

    @classmethod
    def quota_get(cls, user_id, resource):
        with db_session.transactional() as session:
            query = session.query(Quota).filter_by(user_id=user_id,
                                                   resource=resource)
            result = query.first()
        return result

    @classmethod
    def get_user_quotas(cls, user_id):
        with db_session.transactional() as session:
            query = session.query(Quota).filter_by(user_id=user_id).\
                order_by('resource')
            result = query.all()
            quotas = [{'resource': item.resource, 'hard_limit': item.hard_limit}
                      for item in result]
        return quotas

    @classmethod
    def get_user_quotas_for_ui(cls, user_id):
        with db_session.transactional() as session:
            query = session.query(Quota).filter_by(user_id=user_id).\
                filter(Quota.resource != 'instance_attach_ports').\
                filter(Quota.resource != 'instance_attach_volumes').\
                order_by('resource')
            result = query.all()
            quotas = [{'resource': item.resource, 'hard_limit': item.hard_limit}
                      for item in result]
        return quotas

    @classmethod
    def quota_create(cls, user_id, resource, limit):
        with db_session.transactional() as session:
            query = session.query(Quota).filter_by(user_id=user_id,
                                                   resource=resource)
            quota = query.first()
            quota.resource = resource
            quota.hard_limit = limit
            # if quota:
            #     return
            quota = Quota(user_id=user_id,
                          resource=resource,
                          hard_limit=limit)
            quota.save(session)
        return quota

    @classmethod
    def quota_update(cls, user_id, resource, limit):
        with db_session.transactional() as session:
            query = session.query(Quota).filter_by(user_id=user_id,
                                                   resource=resource)
            result = query.update({'hard_limit': limit})
        if not result:
            return False
        return True

    @classmethod
    def update_quotas(cls, user_id, resources):
        with db_session.transactional() as session:
            origin_resources = session.query(Quota).\
                filter(Quota.user_id == user_id,
                       Quota.resource.in_(resources.keys())).all()
            for item in origin_resources:
                if item.hard_limit == resources[item.resource]:
                    continue
                result = cls.quota_update(user_id,
                                          item.resource,
                                          resources[item.resource])
                if not result:
                    return result
            return True

    @classmethod
    def quota_usage_get(cls, user_id, resource):
        pass

    @classmethod
    def quota_usage_create(cls, user_id, resource, in_use,
                           reserved, until_refresh):
        pass

    @classmethod
    def create_quota_class(cls, resource, hard_limit):
        with db_session.transactional() as session:
            query = session.query(QuotaClass).filter_by(resource=resource)

            result = query.first()
            if result:
                query.update({'hard_limit': hard_limit})
            else:
                quota_class = QuotaClass(resource=resource,
                                         hard_limit=hard_limit)
                quota_class.save(session)

    @classmethod
    def create_quota_classes(cls, resources):
        """
        :param resources: dict, key=resource name, value=hard_limit
        :return: None
        """
        for resource, hard_limit in resources.iteritems():
            cls.create_quota_class(resource, hard_limit)

    """
    # below methods for nebula.core.quota
    """

    @classmethod
    def reservation_expire(cls, context):
        with db_session.transactional() as session:
            current_time = timeutils.utcnow()
            query = session.query(Reservation).\
                filter(Reservation.expire < current_time,
                       Reservation.user_id == context.user_id)
        for reservation in query.join(QuotaUsage).all():
            if reservation.delta >= 0:
                reservation.usage.reserved -= reservation.delta
                session.add(reservation.usage)

        #query.soft_delete(sy)

    @classmethod
    def quota_get_by_user(cls, context, user_id, resource):
        user_id = user_id if user_id else context.user_id
        with db_session.transactional() as session:
            quota = session.query(Quota).filter(Quota.user_id == user_id,
                                                Quota.resource == resource).first()
            if not quota:
                quota = session.query(QuotaClass).\
                    filter(QuotaClass.resource == resource).first()
        return quota

    @classmethod
    def get_quotas_by_user(cls, context, user_id, usages=True):
        user_id = user_id if user_id else context.user_id
        with db_session.transactional() as session:
            quotas = dict()
            user_query = session.query(Quota).\
                filter(Quota.user_id == user_id)
            user_quotas = user_query.all()

            quota_classes = session.query(QuotaClass).filter().all()

            if usages:
                quota_usages = cls._get_user_quota_usages(context,
                                                          session,
                                                          user_id)
            for quota in user_quotas:
                item = dict(limit=quota.hard_limit)
                if usages:
                    item.update({
                        'usages': {
                            'in_use': quota_usages[quota.resource].in_use
                            if quota.resource in quota_usages else 0,
                            'reserved': quota_usages[quota.resource].reserved
                            if quota.resource in quota_usages else 0,
                            'total': quota_usages[quota.resource].total
                            if quota.resource in quota_usages else 0,
                        }
                    })
                quotas[quota.resource] = item

            # quota class ( query quota class usages need count use count())
            for quota in quota_classes:
                item = dict(limit=quota.hard_limit)
                if usages:
                    item.update(dict(usages=dict(
                        in_use=0,
                        reserved=0,
                        total=0
                    )))
                quotas[quota.resource] = item
            return quotas

    @classmethod
    def quota_usages_by_user(cls, context, user_id):
        if user_id is None:
            user_id = context.user_id
        with db_session.transactional() as session:
            quota_usages = session.query(QuotaUsage).\
                filter(QuotaUsage.user_id == user_id).all()
            result = dict()
            for quota_usage in quota_usages:
                result.update({
                    quota_usage.resource: {
                        'in_use': quota_usage.in_use,
                        'reserved': quota_usage.reserved,
                    }
                })

    @classmethod
    def _instance_data_get_for_user(cls, context, user_id, session):
        if user_id is None:
            user_id = context.user_id
        result = session.query(func.count('1'),
                               func.sum(Instance.vcpus),
                               func.sum(Instance.memory_mb)
                               ).\
            filter(Instance.owner_id == user_id).first()
        return result[0] or 0, result[1] or 0, result[2] or 0

    @classmethod
    def _sync_instances(cls, context, user_id, session):
        return dict(zip(('instances', 'cores', 'ram'),
                        cls._instance_data_get_for_user(context,
                                                        user_id, session)))

    @classmethod
    def _images_data_get_for_user(cls, context, user_id, session):
        if user_id is None:
            user_id = context.user_id
        result = session.query(func.count('1')).\
            filter(Image.owner_id == user_id).first()
        return result[0] or 0

    @classmethod
    def _sync_images(cls, context, user_id, session):
        return dict(
            images=cls._images_data_get_for_user(context, user_id, session)
        )

    @classmethod
    def _firewall_data_get_for_user(cls, context, user_id, session):
        if user_id is None:
            user_id = context.user_id
        result = session.query(func.count('1')).\
            filter(SecurityGroup.owner_id == user_id).first()
        return result[0] or 0

    @classmethod
    def _sync_firewalls(cls, context, user_id, session):
        return dict(
            firewalls=cls._firewall_data_get_for_user(context, user_id, session)
        )

    @classmethod
    def _virtual_routers_get_for_user(cls, context, user_id, session):
        if user_id is None:
            user_id = context.user_id
        result = session.query(func.count('1')).\
            filter(Virtualrouter.owner_id == user_id).scalar()
        return result or 0

    @classmethod
    def _sync_virtual_routers(cls, context, user_id, session):
        return dict(virtual_routers=cls._virtual_routers_get_for_user(context,
                                                                      user_id,
                                                                      session))

    @classmethod
    def _bandwidth_rx_get_for_user(cls, context, user_id, session):
        if not user_id:
            user_id = context.user_id
        result_rx = session.query(func.sum(Virtualrouter.bandwidth_rx)).\
            filter(Virtualrouter.owner_id == user_id).first()

        return result_rx[0] or 0

    @classmethod
    def _sync_bandwidth_rx(cls, context, user_id, session):
        return dict(bandwidth_rx=cls._bandwidth_rx_get_for_user(context,
                                                                user_id,
                                                                session))

    @classmethod
    def _bandwidth_tx_get_for_user(cls, context, user_id, session):
        if not user_id:
            user_id = context.user_id
        result_tx = session.query(func.sum(Virtualrouter.bandwidth_tx)).\
            filter(Virtualrouter.owner_id == user_id).first()

        return result_tx[0] or 0

    @classmethod
    def _sync_bandwidth_tx(cls, context, user_id, session):
        return dict(bandwidth_tx=cls._bandwidth_tx_get_for_user(context,
                                                                user_id,
                                                                session))

    @classmethod
    def _private_networks_get_for_user(cls, context, user_id, session):
        if not user_id:
            user_id = context.user_id
        result = session.query(func.count(Network.id)).\
            filter(Network.owner_id == user_id).first()

        return result[0] or 0

    @classmethod
    def _sync_private_networks(cls, context, user_id, session):
        return dict(private_networks=cls._private_networks_get_for_user(
            context,
            user_id,
            session)
        )

    @classmethod
    def _binding_publicips_get_for_user(cls, context, user_id, session):
        if not user_id:
            user_id = context.user_id
        result = session.query(func.count(VirtualrouterPublicIP.id)).\
            filter(VirtualrouterPublicIP.owner_id == user_id).scalar()
        return result or 0


    @classmethod
    def _sync_binding_publicips(cls, context, user_id, session):
        binding_publicips = cls._binding_publicips_get_for_user(context,
                                                                user_id,
                                                                session)
        return dict(binding_publicips=binding_publicips)

    @classmethod
    def _binding_private_networks_get_for_user(cls, context, user_id, session):
        return 0

    @classmethod
    def _sync_binding_private_networks(cls, context, user_id, session):
        binding_private_networks = cls._binding_private_networks_get_for_user(
            context,
            user_id,
            session
        )
        return dict(binding_private_networks=binding_private_networks)

    @classmethod
    def _attach_ports_get_for_user(cls, context, user_id, session):
        return 0

    @classmethod
    def _sync_attach_ports(cls, context, user_id, session):
        attach_ports = cls._attach_ports_get_for_user(
            context,
            user_id,
            session
        )
        return dict(attach_ports=attach_ports)

    @classmethod
    def _instance_attach_volumes_get_for_user(cls, context, user_id, session):
        return 0

    @classmethod
    def _sync_instance_attach_volumes(cls, context, user_id, session):
        instance_attach_volumes = cls._instance_attach_volumes_get_for_user(
            context,
            user_id,
            session
        )
        return dict(instance_attach_volumes=instance_attach_volumes)

    @classmethod
    def _volume_backups_get_for_user(cls, context, user_id, session):
        return 0

    @classmethod
    def _sync_volume_backups(cls, context, user_id, session):
        volume_backups = cls._volume_backups_get_for_user(
            context,
            user_id,
            session
        )
        return dict(volume_backups=volume_backups)

    @classmethod
    def _volumes_get_for_user(cls, context, user_id, session):
        if not user_id:
            user_id = context.user_id
        result = session.query(func.sum(Volume.size)).filter(Volume.owner_id == user_id).scalar()
        return result or 0

    @classmethod
    def _sync_volumes(cls, context, user_id, session):
        return dict(
            volumes=cls._volumes_get_for_user(context,
                                              user_id,
                                              session)
        )

    @classmethod
    def _get_user_quota_usages(cls, context, session, user_id):
        if user_id is None:
            user_id = context.user_id
        query = session.query(QuotaUsage).\
            filter(QuotaUsage.user_id == user_id) #.with_lockmode('update')

        rows = query.all()
        usages = dict()
        for row in rows:
            usages[row.resource] = row
        return usages

    @classmethod
    def _quota_usage_create(cls, context, resource, in_use, reserved,
                            until_refresh, session, user_id):
        if user_id is None:
            user_id = context.user_id
        quota_usage = QuotaUsage(user_id=user_id,
                                 resource=resource,
                                 in_use=in_use,
                                 reserved=reserved,
                                 until_refresh=until_refresh)
        quota_usage.save(session)

        return quota_usage

    @classmethod
    def _reservation_create(cls, context, uuid, quota_usage,
                            user_id, res, delta, expire, session):
        if user_id is None:
            user_id = context.user_id
        reservation = Reservation(
            uuid=uuid,
            usage_id=quota_usage.id,
            user_id=user_id,
            resource=res,
            delta=delta,
            expire=expire
        )
        reservation.save(session)
        return reservation

    @classmethod
    def _quota_reservations_query(cls, context, session, user_id, reservations):
        user_id = context.user_id if user_id is None else user_id
        query = session.query(Reservation).\
            filter(Reservation.uuid.in_(reservations),
                   Reservation.user_id == user_id)
        return query

    @classmethod
    def quota_reserve(cls, context, resources, user_quotas, deltas, expire,
                      until_refresh, max_age, user_id):
        elevated = context.elevated()
        with db_session.transactional() as session:
            if user_id is None:
                user_id = context.user_id
            user_usages = cls._get_user_quota_usages(
                context, session, user_id
            )
            work = set(deltas.keys())
            while work:
                resource = work.pop()
                refresh = False
                if ((resource not in PER_QUOTAS) and
                        (resource not in user_usages)):
                    user_usages[resource] = cls._quota_usage_create(
                        elevated,
                        resource,
                        0,
                        0,
                        until_refresh or None,
                        session,
                        user_id)
                    refresh = True
                elif ((resource in PER_QUOTAS) and
                        (resource not in user_usages)):
                    user_usages[resource] = cls._quota_usage_create(
                        elevated,
                        resource,
                        0,
                        0,
                        until_refresh or None,
                        session,
                        user_id)
                    refresh = True
                elif user_usages[resource].in_use < 0:
                    refresh = True

                elif user_usages[resource].until_refresh is not None:
                    user_usages[resource].until_refresh -= 1
                    if user_usages[resource].until_refresh <= 0:
                        refresh = True
                elif max_age and (user_usages[resource].updated_at -
                                      timeutils.utcnow()).seconds >= max_age:
                    refresh = True

                if refresh:
                    sync = getattr(cls, resources[resource].sync)
                    updates = sync(elevated, user_id, session)
                    for res, in_use in updates.items():
                        if ((res not in PER_QUOTAS) and
                                (res not in user_usages)):
                            user_usages[res] = cls._quota_usage_create(
                                elevated,
                                res,
                                0, 0,
                                until_refresh or None,
                                session,
                                user_id)
                        if ((res in PER_QUOTAS) and
                                (res not in user_usages)):
                            user_usages[res] = cls._quota_usage_create(
                                elevated,
                                res,
                                0, 0,
                                until_refresh or None,
                                session,
                                user_id)
                        if user_usages[res].in_use != in_use:
                            LOG.debug('quota_usages out of sync, updating'
                                      'user_id: %(user_id)'
                                      'resource: %(res)',
                                      {'user_id': user_id, 'res': res})
                        user_usages[res].in_use = in_use
                        user_usages[res].until_refresh = until_refresh or None

                        work.discard(res)

            unders = [res for res, delta in deltas.items()
                      if delta < 0 and
                      delta + user_usages[res].in_use < 0]

            overs = [res for res, delta in deltas.items()
                     if user_quotas[res] >= 0 and
                     (user_quotas[res] < delta + user_usages[res].total)]

            if not overs:
                reservations = []
                for res, delta in deltas.items():
                    reservation = cls._reservation_create(
                        elevated,
                        str(uuid.uuid1()),
                        user_usages[res],
                        user_id,
                        res,
                        delta,
                        expire,
                        session
                    )
                    reservations.append(reservation.uuid)

                    if delta > 0:
                        user_usages[res].reserved += delta
            for usage_ref in user_usages.values():
                    session.add(usage_ref)

            if unders:
                LOG.warning("Change will make usage less than 0 for "
                            "the following resources: %s", unders)

            if overs:
                return None
            return reservations

    @classmethod
    def reservation_commit(cls, context, reservations, user_id):
        if user_id is None:
            user_id = context.user_id
        with db_session.transactional() as session:
            user_usages = cls._get_user_quota_usages(context, session, user_id)
            reservation_query = cls._quota_reservations_query(context,
                                                              session,
                                                              user_id,
                                                              reservations)
            for reservation in reservation_query.all():
                usage = user_usages[reservation.resource]
                if reservation.delta >= 0:
                    usage.reserved -= reservation.delta
                usage.in_use += reservation.delta
            reservation_query.update({'deleted': True},
                                     synchronize_session=False)

    @classmethod
    def reservation_rollback(cls, context, reservations, user_id):
        if user_id is None:
            user_id = context.user_id
        with db_session.transactional() as session:
            user_usages = cls._get_user_quota_usages(context, session, user_id)
            reservation_query = cls._quota_reservations_query(context,
                                                              session,
                                                              user_id,
                                                              reservations)
            for reservation in reservation_query.all():
                usage = user_usages[reservation.resource]
                if reservation.delta >= 0:
                    usage.reserved -= reservation.delta
            reservation_query.update({'deleted': True},
                                     synchronize_session=False)

    @classmethod
    def quota_usage_update(cls, context, user_id, resource, in_use):
        pass

    @classmethod
    def _create_default_quota(cls, session, user_id, resource, limit):
        quota = Quota(
            resource=resource,
            hard_limit=limit,
            user_id=user_id
        )
        quota.save(session)

    @classmethod
    def _create_default_quota_class(cls, session, resource, limit):
        quota_class = session.query(QuotaClass).\
            filter(QuotaClass.resource == resource).first()
        if not quota_class:
            quota_class = QuotaClass(
                resource=resource,
                hard_limit=limit
            )
            quota_class.save(session)
        return quota_class

    @classmethod
    def create_default_quotas(cls, context, resources, user_id):
        """
        Create Default quotas
        :param context:
        :param resources:
        :param user_id:
        :return:
        """
        if user_id is None:
            user_id = context.user_id
        with db_session.transactional() as session:
            for res, value in resources.iteritems():
                if value['is_system']:
                    cls._create_default_quota_class(session,
                                                    res,
                                                    value['limit'])
                else:
                    cls._create_default_quota(session,
                                              user_id,
                                              res,
                                              value['limit'])




