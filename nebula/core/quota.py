# -*- coding: utf-8 -*-
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Quotas for instances, and floating ips."""

import datetime
import logging

from oslo.config import cfg
import six

from nebula.core.db import exception
from nebula.core.i18n import _
from nebula.openstack.common import importutils
from nebula.openstack.common import timeutils
from nebula.core.managers import managers
from nebula.core.constants import QUOTA_USER_LEVEL, QUOTA_SYSTEM_LEVEL

LOG = logging.getLogger(__name__)

quota_opts = [
    cfg.IntOpt('quota_instances',
               default=10,
               help='Number of instances allowed per project'),
    cfg.IntOpt('quota_cores',
               default=20,
               help='Number of instance cores allowed per project'),
    cfg.IntOpt('quota_ram',
               default=50 * 1024,
               help='Megabytes of instance RAM allowed per project'),
    cfg.IntOpt('quota_images',
               default=10,
               help='Number of private images'),
    cfg.IntOpt('quota_floating_ips',
               default=10,
               help='Number of floating IPs allowed per project'),
    cfg.IntOpt('quota_fixed_ips',
               default=-1,
               help=('Number of fixed IPs allowed per project (this should be '
                     'at least the number of instances allowed)')),
    cfg.IntOpt('quota_metadata_items',
               default=128,
               help='Number of metadata items allowed per instance'),
    cfg.IntOpt('quota_injected_files',
               default=5,
               help='Number of injected files allowed'),
    cfg.IntOpt('quota_injected_file_content_bytes',
               default=10 * 1024,
               help='Number of bytes allowed per injected file'),
    cfg.IntOpt('quota_injected_file_path_length',
               default=255,
               deprecated_name='quota_injected_file_path_bytes',
               help='Length of injected file path'),
    # cfg.IntOpt('quota_instance_attach_volumes',
    #            default=60,
    #            help='Number of instance attach volume'),
    cfg.IntOpt('quota_instance_attach_ports',
               default=2,
               help='Number of instance attach port'),
    cfg.IntOpt('quota_instance_backups',
               default=5,
               help='Number of instance backups'),
    # cfg.IntOpt('quota_volume_backups',
    #            default=50,
    #            help='Number of volume backups'),
    cfg.IntOpt('quota_volume_capacity',
               default=500,
               help='Max Capacity of volume'),
    cfg.IntOpt('quota_instance_cores_min',
               default=1,
               help='instance cores range min value'),
    cfg.IntOpt('quota_instance_cores_max',
               default=32,
               help='instance cores range max value'),
    cfg.IntOpt('quota_instance_ram_min',
               default=1024,
               help='instance ram range max value'),
    cfg.IntOpt('quota_instance_ram_max',
               default=1024 * 16,
               help='instance cores range max value'),
    cfg.IntOpt('quota_instance_batches',
               default=1,
               help='instance batches value'),
    cfg.IntOpt('quota_network_vlan_min',
               default=2,
               help='instance ram range max value'),
    cfg.IntOpt('quota_network_vlan_max',
               default=4093,
               help='instance cores range max value'),
    cfg.IntOpt('quota_virtual_routers',
               default=10,
               help='Number of virtual routers'),
    cfg.IntOpt('quota_firewalls',
               default=10,
               help='Number of Firewall'),
    cfg.IntOpt('reservation_expire',
               default=86400,
               help='Number of seconds until a reservation expires'),
    cfg.IntOpt('until_refresh',
               default=0,
               help='Count of reservations until usage is refreshed'),
    cfg.IntOpt('max_age',
               default=0,
               help='Number of seconds between subsequent usage refreshes'),
    cfg.StrOpt('quota_driver',
               default='nebula.core.quota.DbQuotaDriver',
               help='Default driver to use for quota checks'),
    cfg.IntOpt('quota_bandwidth_tx',
               default=100,
               help='Number of virtual router bandwidth_tx'),
    cfg.IntOpt('quota_bandwidth_rx',
               default=100,
               help='Number of virtual router bandwidth_rx'),
    cfg.IntOpt('quota_binding_publicips',
               default=10,
               help='Number of binding_publicips'),
    cfg.IntOpt('quota_private_networks',
               default=10,
               help='Number of private networks'),
    cfg.IntOpt('quota_volumes',
               default=1000,
               help='Number of volumes'),
    cfg.IntOpt('quota_binding_private_networks',
               default=5,
               help='Number of binding private networks'),
    cfg.IntOpt('quota_instance_attach_volumes',
               default=5,
               help='Number of instance attach volume'),
    cfg.IntOpt('quota_volume_backups',
               default=5,
               help='Number of volume backups'),
    cfg.IntOpt('quota_system_cores',
               default=10000,
               help='Number of system cores'),
    cfg.IntOpt('quota_system_ram',
               default=100000,
               help='Number of system ram'),
    cfg.IntOpt('quota_system_local_storage',
               default=100000,
               help='Number of local storage'),
]

CONF = cfg.CONF
CONF.register_opts(quota_opts, group="quota")


class DbQuotaDriver(object):
    """Driver to perform necessary checks to enforce quotas and obtain
    quota information.  The default driver utilizes the local
    database.
    """
    UNLIMITED_VALUE = -1

    def get_defaults(self, context, resources):
        """Given a list of resources, retrieve the default quotas.
        Use the class quotas named `_DEFAULT_QUOTA_NAME` as default quotas,
        if it exists.

        :param context: The request context, for access checks.
        :param resources: A dictionary of the registered resources.
        """

        quotas = {}

        for resource in resources.values():
            quotas[resource.name] = CONF.quota.get(resource.flag)
        return quotas

    def get_class_quotas(self, context, resources):
        return managers.quotas.get_class_quotas(context, resources)

    def _process_quotas(self, context, resources, quotas,
                        defaults=True, usages=None,
                        remains=False):
        modified_quotas = {}
        # Get the quotas for the appropriate class.  If the project ID
        # matches the one in the context, we use the quota_class from
        # the context, otherwise, we use the provided quota_class (if
        # any)
        default_quotas = self.get_defaults(context, resources)

        for resource in resources.values():
            # Omit default/quota class values
            if not defaults and resource.name not in quotas:
                LOG.error(resource.name)
                continue

            # Include usages if desired.  This is optional because one
            # internal consumer of this interface wants to access the
            # usages directly from inside a transaction.
            modified_quotas[resource.name] = {
                'limit': quotas[resource.name]
            }
            if usages:
                usage = usages.get(resource.name, {})
                modified_quotas[resource.name].update(
                    in_use=usage.get('in_use', 0),
                    reserved=usage.get('reserved', 0),
                )
            # Initialize remains quotas.
            if remains:
                modified_quotas[resource.name].update(remains=0)

        if remains:
            all_quotas = managers.quotas.quota_get_all(context)
            for quota in all_quotas:
                if quota.resource in modified_quotas:
                    modified_quotas[quota.resource]['remains'] -= \
                        quota.hard_limit
        return modified_quotas

    def get_user_quotas(self, context, resources, user_id, defaults=True,
                        usages=True):
        """Given a list of resources, retrieve the quotas for the given
        user and project.
        :param context: The request context, for access checks.
        :param resources: A dictionary of the registered resources.
        :param user_id: The ID of the user to return quotas for.
        :param defaults: If True, the quota class value (or the
                         default value, if there is no value from the
                         quota class) will be reported if there is no
                         specific value for the resource.
        :param usages: If True, the current in_use and reserved counts
                       will also be returned.
        """
        user_quotas = managers.quotas.get_quotas_by_user(context,
                                                         user_id,
                                                         usages)

        # add default quota in quota/quota_classes
        desired = set(user_quotas.keys())
        need_quotas = [resource for resource in resources
                       if resource not in desired]
        if need_quotas:
            quotas = dict()
            for resource in need_quotas:
                value = dict(
                    limit=self._get_quota_from_conf(resource),
                    is_system=True if resource in QUOTA_SYSTEM_LEVEL else False
                )
                if usages:
                    value.update({
                        'usages': {
                            'in_use': 0,
                            'reserved': 0,
                            'total': 0,
                        }
                    })
                quotas[resource] = value
            managers.quotas.create_default_quotas(context, quotas, user_id)
            user_quotas.update(quotas)

        # Use the project quota for default user quota.
        # user_usages = None
        # if usages:
        #     user_usages = managers.quotas.quota_usages_by_user(context,
        #                                                        user_id)
        return user_quotas
        # return self._process_quotas(context,
        #                             resources,
        #                             user_quotas,
        #                             defaults=defaults,
        #                             usages=user_usages)

    def _get_quota_from_conf(self, resource):
        conf_name = 'quota_{0}'.format(resource)
        return CONF.quota.get(conf_name)

    def _is_unlimited_value(self, v):
        """A helper method to check for unlimited value.
        """

        return v <= self.UNLIMITED_VALUE

    def _sum_quota_values(self, v1, v2):
        """A helper method that handles unlimited values when performing
        sum operation.
        """

        if self._is_unlimited_value(v1) or self._is_unlimited_value(v2):
            return self.UNLIMITED_VALUE
        return v1 + v2

    def _sub_quota_values(self, v1, v2):
        """A helper method that handles unlimited values when performing
        subtraction operation.
        """

        if self._is_unlimited_value(v1) or self._is_unlimited_value(v2):
            return self.UNLIMITED_VALUE
        return v1 - v2

    def get_settable_quotas(self, context, resources, user_id=None):
        """Given a list of resources, retrieve the range of settable quotas for
        the given user or project.

        :param context: The request context, for access checks.
        :param resources: A dictionary of the registered resources.

        :param user_id: The ID of the user to return quotas for.
        """

        settable_quotas = {}
        project_quotas = self.get_project_quotas(context, resources,
                                                 remains=True)
        if user_id:
            setted_quotas = managers.quotas.\
                quota_get_all_by_project_and_user(context,
                                                  user_id)
            user_quotas = self.get_user_quotas(context, resources, user_id,
                                               user_quotas=setted_quotas)
            for key, value in user_quotas.items():
                maximum = \
                    self._sum_quota_values(project_quotas[key]['remains'],
                                           setted_quotas.get(key, 0))
                minimum = value['in_use'] + value['reserved']
                settable_quotas[key] = {'minimum': minimum, 'maximum': maximum}
        else:
            for key, value in project_quotas.items():
                minimum = \
                    max(int(self._sub_quota_values(value['limit'],
                                                   value['remains'])),
                        int(value['in_use'] + value['reserved']))
                settable_quotas[key] = {'minimum': minimum, 'maximum': -1}
        return settable_quotas

    def _get_quotas(self, context, resources, keys, has_sync, user_id=None):
        """A helper method which retrieves the quotas for the specific
        resources identified by keys, and which apply to the current
        context.

        :param context: The request context, for access checks.
        :param resources: A dictionary of the registered resources.
        :param keys: A list of the desired quotas to retrieve.
        :param has_sync: If True, indicates that the resource must
                         have a sync function; if False, indicates
                         that the resource must NOT have a sync
                         function.
        :param user_id: Specify the user_id if current context
                        is admin and admin wants to impact on
                        common user.
        """
        # Filter resources
        if has_sync:
            sync_filt = lambda x: hasattr(x, 'sync')
        else:
            sync_filt = lambda x: not hasattr(x, 'sync')
        desired = set(keys)
        sub_resources = dict((k, v) for k, v in resources.items()
                             if k in desired and sync_filt(v))

        # Make sure we accounted for all of them...
        if len(keys) != len(sub_resources):
            unknown = desired - set(sub_resources.keys())
            raise exception.QuotaResourceUnknown(unknown=sorted(unknown))

        quotas = self.get_user_quotas(context, sub_resources,
                                      user_id, None, usages=False)

        return dict((k, v['limit']) for k, v in quotas.items())

    def limit_check(self, context, resources, values, user_id=None):
        """Check simple quota limits.

        For limits--those quotas for which there is no usage
        synchronization function--this method checks that a set of
        proposed values are permitted by the limit restriction.

        This method will raise a QuotaResourceUnknown exception if a
        given resource is unknown or if it is not a simple limit
        resource.

        If any of the proposed values is over the defined quota, an
        OverQuota exception will be raised with the sorted list of the
        resources which are too high.  Otherwise, the method returns
        nothing.

        :param context: The request context, for access checks.
        :param resources: A dictionary of the registered resources.
        :param values: A dictionary of the values to check against the
                       quota.
        :param user_id: Specify the user_id if current context
                        is admin and admin wants to impact on
                        common user.
        """

        # Ensure no value is less than zero
        unders = [key for key, val in values.items() if val < 0]
        if unders:
            raise exception.InvalidQuotaValue(unders=sorted(unders))

        # If user id is None, then we use the user_id in context
        if user_id is None:
            user_id = context.user_id

        # Get the applicable quotas
        quotas = self._get_quotas(context, resources, values.keys(),
                                  has_sync=False)
        user_quotas = self._get_quotas(context, resources, values.keys(),
                                       has_sync=False,
                                       user_id=user_id,
                                       )

        # Check the quotas and construct a list of the resources that
        # would be put over limit by the desired values
        overs = [key for key, val in values.items()
                 if quotas[key] >= 0 and quotas[key] < val or
                 (user_quotas[key] >= 0 and user_quotas[key] < val)]
        if overs:
            headroom = {}
            # Check project_quotas:
            for key in quotas:
                if quotas[key] >= 0 and quotas[key] < val:
                    headroom[key] = quotas[key]
            # Check user quotas:
            for key in user_quotas:
                if (user_quotas[key] >= 0 and user_quotas[key] < val and
                            headroom.get(key) > user_quotas[key]):
                    headroom[key] = user_quotas[key]

            raise exception.OverQuota(overs=sorted(overs), quotas=quotas,
                                      usages={}, headroom=headroom)

    def reserve(self, context, resources, deltas, expire=None, user_id=None):
        """Check quotas and reserve resources.

        For counting quotas--those quotas for which there is a usage
        synchronization function--this method checks quotas against
        current usage and the desired deltas.

        This method will raise a QuotaResourceUnknown exception if a
        given resource is unknown or if it does not have a usage
        synchronization function.

        If any of the proposed values is over the defined quota, an
        OverQuota exception will be raised with the sorted list of the
        resources which are too high.  Otherwise, the method returns a
        list of reservation UUIDs which were created.

        :param context: The request context, for access checks.
        :param resources: A dictionary of the registered resources.
        :param deltas: A dictionary of the proposed delta changes.
        :param expire: An optional parameter specifying an expiration
                       time for the reservations.  If it is a simple
                       number, it is interpreted as a number of
                       seconds and added to the current time; if it is
                       a datetime.timedelta object, it will also be
                       added to the current time.  A datetime.datetime
                       object will be interpreted as the absolute
                       expiration time.  If None is specified, the
                       default expiration time set by
                       --default-reservation-expire will be used (this
                       value will be treated as a number of seconds).
        :param user_id: Specify the user_id if current context
                        is admin and admin wants to impact on
                        common user.
        """

        # Set up the reservation expiration
        if expire is None:
            expire = CONF.quota.reservation_expire
        if isinstance(expire, (int, long)):
            expire = datetime.timedelta(seconds=expire)
        if isinstance(expire, datetime.timedelta):
            expire = timeutils.utcnow() + expire
        if not isinstance(expire, datetime.datetime):
            raise exception.InvalidReservationExpiration(expire=expire)

        if user_id is None:
            user_id = context.user_id

        # Get the applicable quotas.
        # NOTE(Vek): We're not worried about races at this point.
        #            Yes, the admin may be in the process of reducing
        #            quotas, but that's a pretty rare thing.
        user_quotas = self._get_quotas(context,
                                       resources,
                                       deltas.keys(),
                                       has_sync=True,
                                       user_id=user_id)

        return managers.quotas.quota_reserve(context,
                                             resources,
                                             user_quotas,
                                             deltas,
                                             expire,
                                             CONF.quota.until_refresh,
                                             CONF.quota.max_age,
                                             user_id=user_id)

    def commit(self, context, reservations, user_id=None):
        """Commit reservations.

        :param context: The request context, for access checks.
        :param reservations: A list of the reservation UUIDs, as
                             returned by the reserve() method.
        :param user_id: Specify the user_id if current context
                        is admin and admin wants to impact on
                        common user.
        """

        # If user_id is None, then we use the user_id in context
        if user_id is None:
            user_id = context.user_id

        managers.quotas.reservation_commit(context,
                                           reservations,
                                           user_id=user_id)

    def rollback(self, context, reservations, user_id=None):
        """Roll back reservations.

        :param context: The request context, for access checks.
        :param reservations: A list of the reservation UUIDs, as
                             returned by the reserve() method.
        :param user_id: Specify the user_id if current context
                        is admin and admin wants to impact on
                        common user.
        """
        # If user_id is None, then we use the user_id in context
        if user_id is None:
            user_id = context.user_id

        managers.quotas.reservation_rollback(context,
                                             reservations,
                                             user_id=user_id)

    def usage_reset(self, context, resources):
        """Reset the usage records for a particular user on a list of
        resources.  This will force that user's usage records to be
        refreshed the next time a reservation is made.

        Note: this does not affect the currently outstanding
        reservations the user has; those reservations must be
        committed or rolled back (or expired).

        :param context: The request context, for access checks.
        :param resources: A list of the resource names for which the
                          usage must be reset.
        """

        # We need an elevated context for the calls to
        # quota_usage_update()
        elevated = context.elevated()

        for resource in resources:
            try:
                # Reset the usage to -1, which will force it to be
                # refreshed
                managers.quotas.quota_usage_update(elevated,
                                                   context.user_id,
                                                   resource,
                                                   in_use=-1)
            except exception.QuotaUsageNotFound:
                # That means it'll be refreshed anyway
                pass

    def destroy_all_by_user(self, context, user_id):
        """Destroy all quotas, usages, and reservations associated with a user.

        :param context: The request context, for access checks.

        :param user_id: The ID of the user being deleted.
        """

        managers.quotas.quota_destroy_all_by_user(context,
                                                  user_id)

    def expire(self, context):
        """Expire reservations.

        Explores all currently existing reservations and rolls back
        any that have expired.

        :param context: The request context, for access checks.
        """

        managers.quotas.reservation_expire(context)


class BaseResource(object):
    """Describe a single resource for quota checking."""

    def __init__(self, name, flag=None):
        """Initializes a Resource.

        :param name: The name of the resource, i.e., "instances".
        :param flag: The name of the flag or configuration option
                     which specifies the default value of the quota
                     for this resource.
        """

        self.name = name
        self.flag = flag

    def quota(self, driver, context, **kwargs):
        """Given a driver and context, obtain the quota for this
        resource.

        :param driver: A quota driver.
        :param context: The request context.
        :param quota_class: The quota class corresponding to the
                            project, or for which the quota is to be
                            looked up.  If not provided, it is taken
                            from the context.  If it is given as None,
                            no quota class-specific quota will be
                            searched for.  Note that the quota class
                            defaults to the value in the context,
                            which may not correspond to the project if
                            project_id is not the same as the one in
                            the context.
        """

        # Ditto for the quota class
        quota_class = kwargs.get('quota_class', context.quota_class)

        # Try for the quota class
        if quota_class:
            try:
                return driver.get_by_class(context, quota_class, self.name)
            except exception.QuotaClassNotFound:
                pass

        # OK, return the default
        return self.default

    @property
    def default(self):
        """Return the default value of the quota."""

        return CONF[self.flag] if self.flag else -1


class ReservableResource(BaseResource):
    """Describe a reservable resource."""

    def __init__(self, name, sync, flag=None):
        """Initializes a ReservableResource.

        Reservable resources are those resources which directly
        correspond to objects in the database, i.e., instances,
        cores, etc.

        Usage synchronization function must be associated with each
        object. This function will be called to determine the current
        counts of one or more resources. This association is done in
        database backend.

        The usage synchronization function will be passed three
        arguments: an admin context, the project ID, and an opaque
        session object, which should in turn be passed to the
        underlying database function.  Synchronization functions
        should return a dictionary mapping resource names to the
        current in_use count for those resources; more than one
        resource and resource count may be returned.  Note that
        synchronization functions may be associated with more than one
        ReservableResource.

        :param name: The name of the resource, i.e., "volumes".
        :param sync: A dbapi methods name which returns a dictionary
                     to resynchronize the in_use count for one or more
                     resources, as described above.
        :param flag: The name of the flag or configuration option
                     which specifies the default value of the quota
                     for this resource.
        """
        super(ReservableResource, self).__init__(name, flag=flag)
        self.sync = sync


class AbsoluteResource(BaseResource):
    """Describe a non-reservable resource."""

    pass


class CountableResource(AbsoluteResource):
    """Describe a resource where the counts aren't based solely on the
    project ID.
    """

    def __init__(self, name, count, flag=None):
        """Initializes a CountableResource.

        Countable resources are those resources which directly
        correspond to objects in the database, i.e., instances, cores,
        etc., but for which a count by project ID is inappropriate.  A
        CountableResource must be constructed with a counting
        function, which will be called to determine the current counts
        of the resource.

        The counting function will be passed the context, along with
        the extra positional and keyword arguments that are passed to
        Quota.count().  It should return an integer specifying the
        count.

        Note that this counting is not performed in a transaction-safe
        manner.  This resource class is a temporary measure to provide
        required functionality, until a better approach to solving
        this problem can be evolved.

        :param name: The name of the resource, i.e., "instances".
        :param count: A callable which returns the count of the
                      resource.  The arguments passed are as described
                      above.
        :param flag: The name of the flag or configuration option
                     which specifies the default value of the quota
                     for this resource.
        """

        super(CountableResource, self).__init__(name, flag=flag)
        self.count = count


class QuotaEngine(object):
    """Represent the set of recognized quotas."""

    def __init__(self, quota_driver_class=None):
        """Initialize a Quota object."""
        self._resources = {}
        self._driver_cls = quota_driver_class
        self.__driver = None

    @property
    def _driver(self):
        if self.__driver:
            return self.__driver
        if not self._driver_cls:
            self._driver_cls = CONF.quota.quota_driver
        if isinstance(self._driver_cls, six.string_types):
            self._driver_cls = importutils.import_object(self._driver_cls)
        self.__driver = self._driver_cls
        return self.__driver

    def __contains__(self, resource):
        return resource in self._resources

    def register_resource(self, resource):
        """Register a resource."""

        self._resources[resource.name] = resource

    def register_resources(self, resources):
        """Register a list of resources."""

        for resource in resources:
            self.register_resource(resource)

    def get_by_user(self, context, user_id, resource):
        quota = self._driver.get_by_user(context, user_id, resource)
        if not quota:
            if resource in QUOTA_USER_LEVEL:
                pass
            else:
                pass
        return quota

    def get_by_class(self, context, quota_class, resource):
        """Get a specific quota by quota class."""

        return self._driver.get_by_class(context, quota_class, resource)

    def get_defaults(self, context):
        """Retrieve the default quotas.

        :param context: The request context, for access checks.
        """

        #return self._driver.get_defaults(context, self._resources)
        quotas = {}

        for resource in self._resources.itervalues():
            quotas[resource.name] = dict(
                hard_limit=CONF.quota.get(resource.flag),
                in_use=0)
        return quotas

    def get_class_quotas(self, context, resources=None):

        return self._driver.get_class_quotas(context, resources)

    def get_user_quotas(self, context, user_id, defaults=True, usages=True):
        """Retrieve the quotas for the given user.

        :param context: The request context, for access checks.

        :param user_id: The ID of the user to return quotas for.
        :param defaults: If True, the quota class value (or the
                         default value, if there is no value from the
                         quota class) will be reported if there is no
                         specific value for the resource.
        :param usages: If True, the current in_use and reserved counts
                       will also be returned.
        """

        return self._driver.get_user_quotas(context, self._resources,
                                            user_id,
                                            defaults=defaults,
                                            usages=usages)

    def get_by_user(self, context, user_id, resources, usages=True):
        user_quotas = self.get_user_quotas(context, user_id, usages=usages)
        quotas = {}
        for resource in resources:
            if resource in user_quotas:
                quotas.update({
                    resource: user_quotas[resource]
                })
        return quotas

    def get_settable_quotas(self, context,  user_id=None):
        """Given a list of resources, retrieve the range of settable quotas for
        the given user or project.

        :param context: The request context, for access checks.
        :param resources: A dictionary of the registered resources.
        :param user_id: The ID of the user to return quotas for.
        """

        return self._driver.get_settable_quotas(context,
                                                self._resources,
                                                user_id=user_id)

    def count(self, context, resource, *args, **kwargs):
        """Count a resource.

        For countable resources, invokes the count() function and
        returns its result.  Arguments following the context and
        resource are passed directly to the count function declared by
        the resource.

        :param context: The request context, for access checks.
        :param resource: The name of the resource, as a string.
        """

        # Get the resource
        res = self._resources.get(resource)
        if not res or not hasattr(res, 'count'):
            raise exception.QuotaResourceUnknown(unknown=[resource])

        return res.count(context, *args, **kwargs)

    def limit_check(self, context, user_id=None, **values):
        """Check simple quota limits.

        For limits--those quotas for which there is no usage
        synchronization function--this method checks that a set of
        proposed values are permitted by the limit restriction.  The
        values to check are given as keyword arguments, where the key
        identifies the specific quota limit to check, and the value is
        the proposed value.

        This method will raise a QuotaResourceUnknown exception if a
        given resource is unknown or if it is not a simple limit
        resource.

        If any of the proposed values is over the defined quota, an
        OverQuota exception will be raised with the sorted list of the
        resources which are too high.  Otherwise, the method returns
        nothing.

        :param context: The request context, for access checks.
        :param user_id: Specify the user_id if current context
                        is admin and admin wants to impact on
                        common user.
        """

        return self._driver.limit_check(context,
                                        self._resources,
                                        values,
                                        user_id=user_id)

    def reserve(self, context, expire=None, user_id=None,
                **deltas):
        """Check quotas and reserve resources.

        For counting quotas--those quotas for which there is a usage
        synchronization function--this method checks quotas against
        current usage and the desired deltas.  The deltas are given as
        keyword arguments, and current usage and other reservations
        are factored into the quota check.

        This method will raise a QuotaResourceUnknown exception if a
        given resource is unknown or if it does not have a usage
        synchronization function.

        If any of the proposed values is over the defined quota, an
        OverQuota exception will be raised with the sorted list of the
        resources which are too high.  Otherwise, the method returns a
        list of reservation UUIDs which were created.

        :param context: The request context, for access checks.
        :param expire: An optional parameter specifying an expiration
                       time for the reservations.  If it is a simple
                       number, it is interpreted as a number of
                       seconds and added to the current time; if it is
                       a datetime.timedelta object, it will also be
                       added to the current time.  A datetime.datetime
                       object will be interpreted as the absolute
                       expiration time.  If None is specified, the
                       default expiration time set by
                       --default-reservation-expire will be used (this
                       value will be treated as a number of seconds).
        """
        reservations = self._driver.reserve(context,
                                            self._resources,
                                            deltas,
                                            expire=expire,
                                            user_id=user_id)

        LOG.debug("Created reservations %s", reservations)

        return reservations

    def commit(self, context, reservations, user_id=None):
        """Commit reservations.

        :param context: The request context, for access checks.
        :param reservations: A list of the reservation UUIDs, as
                             returned by the reserve() method.
        """

        try:
            self._driver.commit(context, reservations, user_id=user_id)
        except Exception:
            # NOTE(Vek): Ignoring exceptions here is safe, because the
            # usage resynchronization and the reservation expiration
            # mechanisms will resolve the issue.  The exception is
            # logged, however, because this is less than optimal.
            LOG.exception(_("Failed to commit reservations %s"), reservations)
            return
        LOG.debug("Committed reservations %s", reservations)

    def rollback(self, context, reservations, user_id=None):
        """Roll back reservations.

        :param context: The request context, for access checks.
        :param reservations: A list of the reservation UUIDs, as
                             returned by the reserve() method.
        """

        try:
            self._driver.rollback(context, reservations, user_id=user_id)
        except Exception:
            # NOTE(Vek): Ignoring exceptions here is safe, because the
            # usage resynchronization and the reservation expiration
            # mechanisms will resolve the issue.  The exception is
            # logged, however, because this is less than optimal.
            LOG.exception(_("Failed to roll back reservations %s"),
                          reservations)
            return
        LOG.debug("Rolled back reservations %s", reservations)

    def usage_reset(self, context, resources):
        """Reset the usage records for a particular user on a list of
        resources.  This will force that user's usage records to be
        refreshed the next time a reservation is made.

        Note: this does not affect the currently outstanding
        reservations the user has; those reservations must be
        committed or rolled back (or expired).

        :param context: The request context, for access checks.
        :param resources: A list of the resource names for which the
                          usage must be reset.
        """

        self._driver.usage_reset(context, resources)

    def destroy_all_by_user(self, context, project_id, user_id):
        """Destroy all quotas, usages, and reservations associated with a
        project and user.

        :param context: The request context, for access checks.

        :param user_id: The ID of the user being deleted.
        """
        self._driver.destroy_all_by_user(context, user_id)

    def expire(self, context):
        """Expire reservations.

        Explores all currently existing reservations and rolls back
        any that have expired.

        :param context: The request context, for access checks.
        """

        self._driver.expire(context)

    @property
    def resources(self):
        return sorted(self._resources.keys())


QUOTAS = QuotaEngine()


resources = [
    ReservableResource('instances', '_sync_instances', 'quota_instances'),
    ReservableResource('cores', '_sync_instances', 'quota_cores'),
    ReservableResource('ram', '_sync_instances', 'quota_ram'),
    # for network
    ReservableResource('virtual_routers', '_sync_virtual_routers',
                       'quota_virtual_routers'),
    ReservableResource('private_networks',
                       '_sync_private_networks',
                       'quota_private_networks'),
    ReservableResource('bandwidth_rx', '_sync_bandwidth_rx',
                       'quota_bandwidth_rx'),
    ReservableResource('bandwidth_tx', '_sync_bandwidth_tx',
                       'quota_bandwidth_tx'),
    # ReservableResource('binding_publicips',
    #                    '_sync_binding_publicips',
    #                    'quota_binding_publicips'),
    ReservableResource('images', '_sync_images', 'quota_images'),
    ReservableResource('firewalls', '_sync_firewalls', 'quota_firewalls'),

    # for the one resource quota
    ReservableResource('binding_private_networks',
                       '_sync_binding_private_networks',
                       'quota_binding_private_networks'),
    ReservableResource('instance_attach_volumes',
                       '_sync_instance_attach_volumes',
                       'quota_instance_attach_volumes'),
    ReservableResource('volume_backups',
                       '_sync_volume_backups',
                       'quota_volume_backups'),

    # for volume
    ReservableResource('volumes', '_sync_volumes', 'quota_volumes'),

    # for system count quotas
    CountableResource('system_cores',
                      managers.compute_nodes.vcpu_count,
                      'quota_system_cores'),
    CountableResource('system_ram',
                      managers.compute_nodes.memory_mb_count,
                      'quota_system_ram'),
    CountableResource('system_local_storage',
                      managers.compute_nodes.local_gb_count,
                      'quota_system_local_storage'),

    # CountableResource('security_group_rules',
    #                   db.security_group_rule_count_by_group,
    #                   'quota_security_group_rules'),
    # CountableResource('instance_attach_volumes',
    #                   '',
    #                   'quota_instance_attach_volumes'),
    CountableResource('instance_attach_ports',
                      managers.instances.get_ports_count,
                      'quota_instance_attach_ports'),
    CountableResource('instance_backups',
                      managers.instances.get_backups_count,
                      'quota_instance_backups'),
    CountableResource('volume_backups',
                      managers.volumes.get_backups_count,
                      'quota_volume_backups')
]


QUOTAS.register_resources(resources)
