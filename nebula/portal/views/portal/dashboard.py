# -*- coding: utf-8 -*-
import logging

from nebula.portal.decorators.auth import require_auth
from nebula.portal.views.base import AuthorizedView
from nebula.portal.utils.menu import setMenus

LOG = logging.getLogger(__name__)

#
# 继承 AuthorisedView 授权视图
#
class DashboardView(AuthorizedView):

    template_name = 'home/dashboard.html'

    active_module = 'dashboard'

    def get_context_data(self, **kwargs):

        context = super(DashboardView, self).get_context_data(**kwargs)

        context.update(dict(
            resources=self._get_statistics(),
        ))
        context.update(setMenus())
        return context

    def get(self, **kwargs):
        return self.render_template(self.template_name,
                                    **self.get_context_data(**kwargs))

    def _get_statistics(self):
        return dict()
