视图
==========


Nebula Views采用与Django通用视图相似的方式实现.有着复杂的继承体系, 但最终的视图类只需简单几行代码即可实现对应功能.
可参考 `Classy Class-Based Views <http://ccbv.co.uk/>`_


创建视图
---------

.. autoclass:: nebula.portal.views.base.CreateView

.. autoclass:: nebula.portal.views.base.JsonCreateView

.. autoclass:: nebula.portal.views.base.BuilderCreateView


删除视图
----------

.. autoclass:: nebula.portal.views.base.DeleteView

.. autoclass:: nebula.portal.views.base.BuilderDeleteView


更新视图
----------

.. autoclass:: nebula.portal.views.base.UpdateView

.. autoclass:: nebula.portal.views.base.BuilderUpdateView


详情视图
----------

.. autoclass:: nebula.portal.views.base.DetailView


列表视图
----------

.. autoclass:: nebula.portal.views.base.ListView

.. autoclass:: nebula.portal.views.base.JsonListView
