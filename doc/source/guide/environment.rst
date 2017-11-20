搭建开发环境
============


环境要求
----------

* Python 2.7.5或以上


版本管理
---------

* 版本库地址: `Nebula <http://192.168.0.54/iaas/nebula>`_
* 版本开发方式请遵循 **GitFlow** 规范.


搭建开发环境
-------------

#. 安装virtualenv(推荐在项目根目录下, 创建名为 ``.venv`` 的虚拟环境)

    首先, 安装virtualenv.

    >>> pip install virtualenv -i http://mirrors.aliyun.com/pypi/simple/

    然后创建虚拟机环境.

    >>> virtualenv .venv

    进入virtualenv命令:

    >>> source .venv/bin/activate

    退出virtualenv命令:

    >>> deactivate

#. 安装依赖库

    进入virtualenv:

    >>> source .venv/bin/activate

    在 ``nebula/code`` 目录下执行:

    >>> pip install -r requirements.txt -r local-requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --download-cache=/tmp/

#. 开发代码链接到virtualenv中

    在 ``nebula/code`` 目录下执行:

    >>> pip install -e .


开发配置文件
-------------

请在 ``nebula/code/etc/nebula/`` 目录下, 创建名为 ``nebula.conf`` 文件, 内容如下::

    [DEFAULT]
    deubg=True

    [database]
    # connection=mysql+pymysql://root:openstack@172.17.0.233:3306/nebula?charset=utf8
    # connection=mysql+pymysql://huamon:huamon@localhost:3306/huamon?charset=utf8
    connection=mysql+pymysql://nebula:nebula@192.168.1.22:3306/nebula?charset=utf8

    [chameleon]
    messaging_urls='amqp://guest:openstack@172.16.40.25:5672//'

    [portal]
    address=0.0.0.0
    REDIS_HOST=192.168.1.22
    REDIS_PORT=6379
    REDIS_DB=0
    REDIS_PASSWORD=123456

    [missions]
    BROKER_URL=amqp://guest@localhost//
    BROKER_API=amqp://guest@localhost@192.168.1.22:15672/api/
    # BROKER_URL=amqp://nebula:nebula@192.168.1.22//
    # BROKER_API=amqp://nebula:nebula@192.168.1.22:15672/api/

    [service_credentials]
    #
    # Options defined in nebula.core.openstack_clients.options
    #
    timeout=30
    username=admin
    password=admin
    tenant_name=admin
    tenant_id=065e24d5f4db4733b98f40dae41fd71d
    auth_url=http://172.16.40.25:5000/v2.0
    nova_endpoint=http://172.16.40.25:8774/v2/065e24d5f4db4733b98f40dae41fd71d
    glance_endpoint=http://172.16.40.25:9292
    neutron_endpoint=http://172.16.40.25:9696
    cinder_endpoint=http://172.16.40.25:8776/v1/065e24d5f4db4733b98f40dae41fd71d

    [quota]
    quota_driver = nebula.core.quota.DbQuotaDriver


运行开发服务器
---------------

#. 在 ``nebula/code/`` 目录下运行命令 ``invoke -l`` , 查看目前支持的开发命令(具体内容会更加代码更新产品变化)::

    > invoke -l

    Available tasks:

      db.create
      db.create_permission
      db.create_user
      db.drop
      db.dump
      doc.build (doc)
      server.missions
      server.testweb (server)
      test.all (test)
      test.models
      test.views


#. 运行 ``invoke server`` 启动测试服务器::

    > invoke server

    2014-07-03 09:26:44.332 64734 INFO werkzeug [-]  * Running on http://0.0.0.0:8000/
    2014-07-03 09:26:44.356 64734 INFO werkzeug [-]  * Restarting with reloader

#. 运行 ``invoke server.missions`` 启动后台任务服务器( **需要在本地环境, 安装rabbitmq server** )
