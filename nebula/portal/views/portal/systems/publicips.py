# -*- coding: utf-8 -*-
from nebula.core.forms.form import NebulaForm
import json
import socket
import struct
from flask import request
from flask import jsonify
from flask import flash
from wtforms import (
    validators,
    StringField,
    IntegerField,
)

from nebula.core.i18n import _
from .base import SystemMixin
from nebula.core.db import session as db_session
from nebula.core.models import VirtualrouterNetwork
from nebula.core import VirtualrouterPublicIP
from nebula.core import VirtualrouterFloatingIP
from nebula.core.managers import managers
from nebula.portal.views.base import(
    CreateView,
    JsonCreateView,
    ListView,
    DeleteView,
    UpdateView
)
from nebula.core.mission.flows.networks.create_publicip import VirtualrouterFloatingIPCreateBuilder

"""
    注意：这个类没有被用了！
"""

def ip2long(ip):
    """
    Convert an IP string to long
    """
    packed_ip = socket.inet_aton(ip)
    return struct.unpack("!L", packed_ip)[0]


def long2ip(num):
    """
    Convert an long to string ip
    """
    return socket.inet_ntoa(struct.pack('!L', num))


class FloatingipMixin(object):
    active_module = 'float_ip'


class PublicIPCreateForm(NebulaForm):

    network_id = IntegerField(u'外部网络',
                            validators=[validators.optional()])

"""
Public IP Form & View
"""


class PublicIPCreateFormView(CreateView):

    template_name = 'systems/form/create_publicip.html'
    form_class = PublicIPCreateForm
    model_class = VirtualrouterFloatingIP

    def get_context_data(self, **context):
        context = super(PublicIPCreateFormView, self).get_context_data(**context)
        context.update({
            'ext_networks': managers.private_networks.get_external_network(self.context)
        })

        return context


class PublicIPUpdateFormView(UpdateView):

    template_name = 'systems/form/update_publicip.html'
    form_class = PublicIPCreateForm
    model_class = VirtualrouterFloatingIP
    context_object_name = 'virtualrouter_floatingip'

    def get_context_data(self, **context):
        context = super(PublicIPUpdateFormView, self).get_context_data(**context)
        context.update({
            'users': managers.users.get_all_by_active(),
        })
        return context


class PublicIPCreateView(JsonCreateView):

    form_class = PublicIPCreateForm
    model_class = VirtualrouterFloatingIP
    builder_class = VirtualrouterFloatingIPCreateBuilder

class PublicIpUpdateView(UpdateView):

    def post(self, *args, **kwargs):
        result = dict(
            code=1,
            message=u'success'
        )
        try:
            public_ip_id = kwargs.get("id")
            params = json.loads(request.get_data())
            owner_id = params.get("owner_id", None)
            if not owner_id:
                raise Exception(u"分配用户不能为空")
            managers.virtualrouter_publicips.update(self.context,
                                                    public_ip_id,
                                                    dict(owner_id=owner_id))
        except Exception as err:
            result.update(dict(
                code=0,
                message=u'公网IP更新失败：%s' % err
            ))
        flash(result['message'], category=result['code'])
        return jsonify(result)


class UnbindingPublicIpFormView(DeleteView):

    template_name = "systems/form/unbinding_publicip.html"
    model_class = VirtualrouterNetwork
    context_object_name = "virtualrouter_network"


class PublicIPListView(SystemMixin, FloatingipMixin, ListView):

    model_class = VirtualrouterFloatingIP
    template_name = 'systems/publicip_list.html'

    def get_queryset(self):
        return self.model_class.query


class PublicIPSubListView(SystemMixin, FloatingipMixin, ListView):

    model_class = VirtualrouterPublicIP
    template_name = 'systems/_partial/publicip_sub_list.html'

    def get_queryset(self):
        queryset = super(PublicIPSubListView, self).get_queryset()
        virtualrouter_id = request.args['resource_id']
        return queryset.filter_by(virtualrouter_id=virtualrouter_id)


class PublicIpDeleteView(DeleteView):

    def delete(self, *args, **kwargs):
        public_ip_id = kwargs.get('id')
        result = managers.virtualrouter_publicips.delete(public_ip_id)
        flash(result['message'], category=result['code'])
        return jsonify(result)
