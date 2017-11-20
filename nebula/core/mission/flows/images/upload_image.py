# -*- coding: utf-8 -*-

import logging
import os, subprocess
from taskflow import retry
from glanceclient.exc import HTTPNotFound
from taskflow.patterns import linear_flow
from nebula.core.resource_monitor import monitor

from nebula.core.managers import managers
from nebula.core.mission import flow_builder
from nebula.core.mission import task
from nebula.core.openstack_clients import glance
from nebula.core.i18n import _
from nebula.core import constants

from nebula.core.quota import QUOTAS

ACTION = 'image:create'

LOG = logging.getLogger(__name__)


class AddImageTask(task.NebulaTask):
    def __init__(self):
        super(AddImageTask, self).__init__(addons=[ACTION])

    def execute(self, job_id, owner_id, is_super, file_name, resource_id, **kwargs):

        self.update_job_state_desc(job_id, _(u"开始上传镜像"))

        image_create_info = managers.images.get(self.admin_context, resource_id)
        if not image_create_info:
            self.update_job_state_desc(job_id, u'资源不存在')
            raise Exception("资源不存在")

        params = dict(
            disk_format=image_create_info.disk_format,
            container_format=image_create_info.container_format,
            name=image_create_info.name,
            size=image_create_info.size,
            min_disk=image_create_info.min_disk,
            is_public=False,
            min_ram=image_create_info.min_ram
        )

        #添加properties:os_type
        properties = dict(os_type=image_create_info.os_distro,hypervisor_type='qemu')

        #properties["upload_type"] = "1"
        
        #temporary way: hardcode for vmware-image configuration
        if params["disk_format"] == "vmdk":
            properties["hypervisor_type"] = "vmware"
            properties["vmware_adaptertype"] = "lsiLogicsas"
            properties["vmware_disktype"] = "thin"

        #temporary way: hardcode for vmware-image configuration
        
        params.update(dict(properties=properties))

        #获取刚上传镜像文件路径
        image_file_path = os.path.join(constants.UPLOAD_IMG_FILE_PATH,
                                       file_name)
        LOG.info(image_file_path)
        fimage = open(image_file_path, 'rb')
        params.update(dict(data=fimage))
        LOG.info("Upload successed, Begining create image to glance.")

        os.system("sync")
        os.system("echo 3 > /proc/sys/vm/drop_caches")

        image_info = None
        try:
            image_info = glance.get_client().images.create(**params)
            #delete_image_values = dict(image_uuid=image_info.id)
            #images_sync_info=managers.images.get_by(self.admin_context, **delete_image_values)
            #LOG.info("AddImageTask34112::::::::::")
            #if images_sync_info:
            #    LOG.info("AddImageTask34113::::::::::")
            #    managers.images.delete_by(self.admin_context, delete_image_values)
            values = dict(image_uuid=image_info.id, resource_id=resource_id)
            managers.images.update(self.admin_context, **values)
            glance.get_client().images.update(image_info.id, is_public=image_create_info.is_public)
            glance.get_client().images.update(image_info.id, properties=properties)
        except Exception as ex:
            #上传镜像失败，删除数据库中数据
            self.update_job_state_desc(job_id, _(u"底层出错"))
            fimage.close()
            os.remove(image_file_path)
            raise ex

        def checker():
            values = dict(image_uuid=image_info.id)
            image = managers.images.get_by(self.admin_context, **values)
            if image.status == 'active':
                return True
            elif image.status == 'error':
                #底层error，需要先删除底层镜像记录，然后删除nebula镜像记录
                #删除底层镜像记录
                glance.get_client().images.delete(image.image_uuid)
                raise res_mon.ResourceFailureError('Error InstanceBackup ConvertImage state')
            return False
        
        try:
            res_mon = monitor.ResourceChangeMonitor(checker)
            res_mon.wait(10800)
            fimage.close()
            os.system("sync")
            os.system("echo 3 > /proc/sys/vm/drop_caches")
            os.remove(image_file_path)
        except Exception as ex:
            fimage.close()
            #超时需先删除底层镜像记录，然后删除nebula镜像记录
            #删除底层镜像记录
            glance.get_client().images.delete(image_info.id)
            os.remove(image_file_path)

        self.update_job_state_desc(job_id, _(u"上传镜像成功"))

    def revert(self, job_id, *args, **kwargs):
        self.log_current_task_failures(*args, **kwargs)
        self.update_job_state_desc(job_id, _(u"上传镜像失败"))


def get_flow():
    flow = linear_flow.Flow(ACTION)
    flow.add(AddImageTask())
    return flow


class UserImageUploadBuilder(flow_builder.Builder):
    def __init__(self, context, resource_kwargs=None, store=None):
        super(UserImageUploadBuilder, self).__init__(
            context,
            resource_kwargs=resource_kwargs,
            flow_factory=get_flow,
            store=store)
        
    def get_size(self, file_name):
        image_file_path = os.path.join(constants.UPLOAD_IMG_FILE_PATH,str(file_name))

        cmd = "qemu-img info %s |grep virtual | cut -d '(' -f2 | cut -d ' ' -f1" % image_file_path
        LOG.info(cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        line = p.stdout.readlines()
        line = line[0].replace("\n", "")
        size = line
        LOG.info(size)

        return size

    def prepare_resource(self, *args, **kwargs):
        store_data = dict(
            image_name=kwargs['name'],
            owner_id=self.context.user_id,
            file_name=kwargs['file_name'],
            is_super=self.context.is_super
        )
        
        #取得磁盘的虚拟大小
        kwargs['min_disk'] = self.get_size(kwargs['file_name'])

        values = dict(images=1)
        reservations = QUOTAS.reserve(self.context, **values)
        try:
            image = managers.images.create(self.context.user_id, **kwargs)
        except Exception as err:
            LOG.info("Create image faild: %s." % str(err))
            QUOTAS.rollback(self.context, reservations)
            raise err
        else:
            QUOTAS.commit(self.context, reservations)

        self.store.update(store_data)
        return image

    def associate_resource_with_job(self, resource, job):
        managers.images.update_by_id(self.context,
                                     resource.id,
                                     dict(job_id=job.id))
