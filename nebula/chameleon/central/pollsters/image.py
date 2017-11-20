# -*- coding: utf-8 -*-
import six

from nebula.chameleon.central import plugin
from nebula.core import models
from nebula.core.db import session as db_session
from nebula.core.openstack_clients import glance
from nebula.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class ImageStatus(plugin.CentralPollster):
    def poll(self, manager, cache):
        images = glance.get_client().images.list()
        image_uuid_to_status = {}
        for image in images:
            image_uuid_to_status[image.id] = image.status

        with db_session.transactional() as session:
            for image_uuid, image_status in six.iteritems(image_uuid_to_status):
                session.query(models.Image) \
                       .filter(models.Image.image_uuid == image_uuid) \
                       .update({models.Image.status: image_status})


class ImageSync(plugin.CentralPollster):
    """
    同步Glance Image
    """
    def poll(self, manager, cache):
        images = glance.get_client().images.list()

        with db_session.transactional() as session:
            for image in filter(lambda i: not hasattr(i, 'base_image_ref'), images):

                LOG.info(image.name)
                LOG.info(image.id)
                assert image.min_disk > 0, u"image's min_disk must geater than 0"
                assert image.properties['os_type'], u"image's os_type must not be None"
                
                image_ref = session.query(models.Image).filter(models.Image.image_uuid == image.id).first()
                if not image_ref and image.is_public:
                    image_ref = models.Image(
                        name=image.name,
                        image_uuid=image.id,
                        disk_format=image.disk_format,
                        container_format=image.container_format,
                        size=image.size,
                        status=image.status,
                        min_disk=image.min_disk,
                        min_ram=image.min_ram,
                        is_public=image.is_public,
                        architecture=self._os_architecture(image.properties['os_type']),
                        os_distro=image.properties['os_type'],
                    )
                    session.add(image_ref)

    def _os_architecture(self, os_type):
        if os_type in ('centos', 'ubuntu', 'redhat'):
            return 'LINUX'
        elif os_type in ('win', 'windows'):
            return 'WINDOWS'
        return 'LINUX'
