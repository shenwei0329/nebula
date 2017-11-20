# -*- coding: utf-8 -*-
__author__ = 'shenwei'

'''2015-9-26 by shenwei @chengdu
    Zabbix json API

    可参考 pyzabbix 包！

    系统运行环境数据须利用这个接口获取，如：服务器个数；CPU个数；内存容量；磁盘空间和网卡及网络等，以及这些资源的使用情况等。

    1) hosts = getHost('')：获取所有 主机名称
    2) for h in hosts：获取每个主机的 信息 [ available, status,

'''

import urllib
import urllib2
import json

class ZabbixAPI(object):

    def __init__(self, url, user, passwd):
        print(">>> ZabbixAPI starting")
        self.url = url
        self.user = user
        self.passwd = passwd
        self.session = ''
        self.id = 1
        self._open()

    def _open(self):
        """
        考虑到在使用中，SESSION会到期，所以需要及时获取新的。
        :return:
        """
        self._get_session()

    def request(self, data):
        """
        发出 REST 请求，并返回响应数据。
        :param data:
        :return:
        """
        headerdata = {"Content-Type":  "application/json"}
        req = urllib2.Request(self.url, headers=headerdata)
        # enable cookie
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        response = opener.open(req, data)
        return json.loads(response.read())

    def _get_session(self):
        """
        获取新的SESSIO。
        :return:
        """
        method = "user.login"
        params = {
                    "user": self.user,
                    "password": self.passwd
                }
        res = self._doCmd(method, params)
        ## print res
        if len(res)>0:
            self.session = res

    def getHost(self, hostname):
        """
        获取监控的 主机 信息。
        :param hostname: 指定主机名，获取该主机信息；或不指定（即＝""时），获取所有主机信息。
        :return:
        """
        method = "host.get"
        params = {
                    "output": "extend",
                    "filter": {"host": hostname}
                }
        return self._doCmd(method, params)

    def _doCmd(self, method, params):
        req_data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "auth": self.session,
                "id": self.id
            })
        self.id += 1
        res = self.request(req_data)
        ## print res
        if res.has_key("result"):
            return res["result"]
        else:
            return ''

if __name__ == '__main__':
    l = ZabbixAPI('http://10.0.1.59:80/zabbix/api_jsonrpc.php', 'admin', 'sw64419')
    hosts = l.getHost('')
    if len(hosts)>0:
        print("> Total: %d" % len(hosts))

        for host in hosts:
            print host
            print("> Host:[%s]" % host['name'])

    host = l.getHost('datanode001')
    print host[0]['hostid']

    method = "item.get"
    params = {
        "hostid": host[0]["hostid"],
        "output": ["itemids","key_","units","lastvalue"]
    }
    res = l._doCmd(method, params)

    for _i in res:
        print(">>> %s[%s]: %s(%s)" % (_i['itemid'],_i['key_'],_i['lastvalue'],_i['units']))
