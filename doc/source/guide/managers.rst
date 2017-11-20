数据库模型Manager
======================

Manager是Model之上的封转层, 接受业务输入参数, 定义数据库操作方法.
**每个Model都应该有一个对应的Manager**


Manager 目录
----------------

``nebula/core/managers/``


Manager定义
----------------

Manager的所有方法都应接受名为context的参数::

    class JobManager(BaseManager):

        def _get(self, context, id, session=None):
            return self.model_query(context, Job, session=session).get(id)

        def get(self, context, id):
            return self._get(context, id)

        def create(self, context, **kwargs):
            session = db_session.get_session()
            create_kwargs = {
                'creator_id': context.user_id,
                'owner_id': context.user_id,
            }
            create_kwargs.update(kwargs)
            job = Job(**create_kwargs)
            job.save(session)
            return job

        def update(self, context, job_id, values):
            session = self.get_session()
            with session.begin():
                job = self._get(context, job_id, session=session)
                job.update(values)

        def update_state_by_flow_uuid(self, context, flow_uuid, state):
            session = self.get_session()
            with session.begin():
                self.model_query(context, Job, session=session) \
                    .filter(Job.flow_uuid == flow_uuid) \
                    .update({'state': state})


Context定义
------------

.. autoclass:: nebula.core.context.RequestContext







