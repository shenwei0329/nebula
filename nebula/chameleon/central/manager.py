# -*- coding: utf-8 -*-
from nebula.chameleon import agent


class AgentManager(agent.AgentManager):
    def __init__(self):
        super(AgentManager, self).__init__('central_pollsters',
                                           'central_pollster_intervals')
