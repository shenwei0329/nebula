# -*- coding: utf-8 -*-
__author__ = 'shenwei'

'''2015-9-22 by shenwei @chengdu
    pip install python-ldap
'''
import ldap
import ldap.modlist as modlist

class LDAP(object):

    def __init__(self, url, user, passwd):
        self.url = url
        self.opened = False
        self.user = user
        self.passwd = passwd

    def _open(self):
        if self.opened:
            self._close()

        try:
            self.conn = ldap.open(self.url)
            self.conn.protocol_version = ldap.VERSION3
            self.opened = True
            ## print 'OK'
        except ldap.LDAPError:
            self.opened = False
        finally:
            return self.opened

    def _close(self):
        if self.opened:
            self.conn.unbind()
            self.opened = False

    def _attach(self):

        if not self._open():
            return False

        try:
            self.conn.simple_bind(self.user, self.passwd)
        except ldap.LDAPError:
            return False
        return True

    def _detach(self):

        if not self.opened:
            return

        self.conn.unbind_s()
        self.opened = False

    def add(self, dn, attrs):
        '''
        添加一个目录项
        :param dn: '...,dc=yun70,dc=com'
        :param attrs: {'objectclass':['top',...],'cn':'...',...}
        :return:
        '''

        if not self._attach():
            return False

        try:
            _ldif = modlist.addModlist(attrs)
            self.conn.add_s(dn, _ldif)
            _ret = True
        except ldap.LDAPError:
            _ret = False
        finally:
            self._detach()
            return _ret

    def delete(self, dn):
        '''
        删除一个目录项
        :param dn: '...,dc=yun70,dc=com'
        :param attrs: {'objectclass':['top',...],'cn':'...',...}
        :return:
        '''

        if not self._attach():
            return False

        try:
            self.conn.delete_s(dn)
            _ret = True
        except ldap.LDAPError:
            _ret = False
        finally:
            self._detach()
            return _ret

    def search_url(self, dn, filter, ou):

        if not self._open():
            return None

        ## print('ou=%s' % ou)

        ldap_result_id = self.conn.search(dn, ldap.SCOPE_SUBTREE, filter, ['l', 'ou'])
        while 1:
            result_type, result_data = self.conn.result(ldap_result_id, 0)
            if result_data == []:
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:

                    ## print result_data

                    if result_data[0][1].has_key('l'):

                        ## print result_data[0][1]['l'][0]

                        if result_data[0][1]['ou'][0] == ou:
                            self._close()
                            return result_data[0][1]['l'][0]
        self._close()
        return None

    def get_rest_api(self, rest_name):
        dn = "ou=rest-api.local,ou=services directory,dc=yun70,dc=com"
        filter = "ou=*"
        return self.search_url(dn, filter, rest_name)

    def get_app_url(self, app_name):
        dn = "ou=applications,ou=web-app,ou=services directory,dc=yun70,dc=com"
        filter = "ou=*"
        return self.search_url(dn, filter, app_name)

    def get_hadoop_url(self, mod_name):
        dn = "ou=hadoop-env,ou=web-app,ou=services directory,dc=yun70,dc=com"
        filter = "ou=*"
        _master = self.search_url(dn, filter, 'master')
        if _master is not None:
            _url = self.search_url(dn, filter, mod_name)
            if _url is not None:
                return str(_url % _master)

if __name__ == '__main__':
    l = LDAP('10.0.1.60', 'cn=Manager,dc=yun70,dc=com', 'sw64419')
    print l.get_rest_api('etl-task-log')
    print l.get_hadoop_url('oozie')
    print l.get_app_url('huaxi')
    dn = "ou=tester,ou=applications,ou=web-app,ou=services directory,dc=yun70,dc=com"
    if not l.add(dn,{'objectclass':['top','organizationalUnit']}):
        print('>>> add entry Error!')
    if not l.delete(dn):
        print(">>> delete entry Error!")
