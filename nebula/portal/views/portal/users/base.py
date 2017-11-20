# -*- coding: utf-8 -*-

import logging

LOG = logging.getLogger(__name__)

from nebula.portal.decorators.auth import require_auth
from nebula.portal.views.base import AuthorizedView


class UserBaseView(AuthorizedView):

    decorators = (require_auth,)

    def __init__(self):
        super(UserBaseView, self).__init__()
        self.show_profile = True
        self.main_menus_mini = True

    def render_template(self, template_name_or_list, **additional_context):

        additional_context.update(
            {'main_menus_mini': True}
        )

        return super(UserBaseView, self).render_template(template_name_or_list,
                                                         **additional_context)


class UserMixin(object):

    decorators = (require_auth,)

    def __init__(self):
        super(UserMixin, self).__init__()
        self.show_profile = True

    def get_context_data(self, **kwargs):
        context = super(UserMixin, self).get_context_data(**kwargs)
        context.update({
            'main_menus_mini': True
        })
        return context
