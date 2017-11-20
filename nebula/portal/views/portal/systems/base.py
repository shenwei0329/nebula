# -*- coding: utf-8 -*-

from flask import session

class SystemMixin(object):
    """
        这个类做什么？
    """

    def _find_system_active(self):
        """
        ？
        :return:
        """
        if not self.active_module:
            return
        for key in self.system_menus.keys():
            for item in self.system_menus[key]:
                item['active'] = self.active_module in item.values()

    def get_context_data(self, **kwargs):
        """
        获取上下文 context
        :param kwargs:
        :return:
        """
        context = super(SystemMixin, self).get_context_data(**kwargs)
        self._find_system_active()
        context.update({
            'main_menus_mini': True,
            'system_menus': self.system_menus,
        })
        return context

class SystemSW(object):

    def get_context_data(self, **kwargs):
        context = super(SystemSW, self).get_context_data(**kwargs)
        context.update({
            'main_menus_mini': True,
        })
        return context