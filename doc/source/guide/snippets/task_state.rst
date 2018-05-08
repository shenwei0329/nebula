资源列表任务状态
================

#. 页面虚拟机资源第二列, 需要统一显示为资源的任务状态, 如图:

    .. image:: ../../_static/virtualrouter_task_state.jpg

#. 实现代码

    #. 调整Table TH::

        <thead>
            <tr>
              <th style="width:1%"> <div class="checkbox check-default">
                  <input id="checkbox10" type="checkbox" value="1" class="checkall">
                  <label for="checkbox10"></label>
                </div>
              </th>
              <th>名称</th>
              <th>任务状态</th> # 调整或添加任务状态为第三个"th"
              <th>上行带宽(Mb/s)</th>
              <th>下行带宽(Mb/s)</th>
              <th>外部IP</th>
              {% if user.is_super %}
              <th>属于者</th>
              {% endif %}
              <th>创建于</th>
            </tr>
        </thead>

    #. 调整Table body::

        <tbody>
            {%- for virtualrouter in pagination.items %}
            # tr添加data-resource-uuid属性, 标识当前resource是否已关联到openstack资源.
            # 如果data-resource-uuid为空, 则在界面上不能进行除删除外的其他操作.
            <tr class="show-others" data-resource-uuid="{{ virtualrouter.virtualrouter_uuid }}">

              <td class="v-align-middle"><div class="checkbox check-default">
                  <input id="checkbox{{ loop.index }}" type="checkbox" value="{{ virtualrouter.id }}">
                  <label for="checkbox{{ loop.index }}"></label>
                </div>
              </td>

              <td><a href="{{ url_for('portal.virtualrouter_detail', id=virtualrouter.id) }}">{{ virtualrouter.name }}</a></td>

              # 第三个td统一显示resource的资源状态.
              # 使用job_state_class过滤器生成css, 使用job_state_humanize生成任务状态描述
              <td class="{{ virtualrouter.job.state | job_state_class }}">
                  {{ virtualrouter.job.state | job_state_humanize }}
              </td>
              <!-- 其他部分省略 -->

            {%- endfor %}
        </tbody>
