




# noinspection PyUnresolvedReferences
from backports.configparser import ConfigParser
import os
import unittest
import warnings
from builtins import int
from builtins import open

import pymysql
from future import standard_library

from pammysqltools.manager import UserManager, GroupManager, GroupListManager

standard_library.install_aliases()


class ManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = ConfigParser()
        cls.config.read([r'pam_mysql_manager-test.conf', r'/etc/pam_mysql_manager-test.conf',
                         os.path.expanduser('~/.pam_mysql_manager-test.conf')])

        mysql_user = os.getenv("PAMMYSQL_TEST_MYSQL_USER", cls.config.get('database', 'user', fallback='root'))
        mysql_pass = os.getenv("PAMMYSQL_TEST_MYSQL_PASS", cls.config.get('database', 'password', fallback=''))
        mysql_host = os.getenv("PAMMYSQL_TEST_MYSQL_HOST", cls.config.get('database', 'host', fallback='localhost'))
        mysql_port = int(os.getenv("PAMMYSQL_TEST_MYSQL_PORT", cls.config.get('database', 'port', fallback="3306")))
        mysql_db = os.getenv("PAMMYSQL_TEST_MYSQL_DB", cls.config.get('database', 'database', fallback='auth_test'))

        cls.dbs = pymysql.connect(host=mysql_host,
                                  user=mysql_user,
                                  password=mysql_pass,
                                  db=mysql_db,
                                  port=mysql_port)

        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdb.sql"), "r") as f:
            cls.sql = f.read()

    def setUp(self):
        with self.dbs.cursor() as cur:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                cur.execute(self.sql)

    def tearDown(self):
        self.dbs.rollback()

    @classmethod
    def tearDownClass(cls):
        cls.dbs.close()


class UserManagerTests(ManagerTests):
    testuser = {'username': 'testuser', 'mini': 1, 'shell': '/bin/sh', 'homedir': '/home/testuser', 'lstchg': 0,
                'maxi': 2, 'warn': 3, 'flag': 6, 'gid': 1000, 'gecos': 'Testuser', 'expire': 5, 'inact': 4,
                'password': 'ABCD', 'uid': 1000}
    testuser2 = {'username': 'testuser2', 'mini': 8, 'shell': '/bin/bash', 'homedir': '/home/testuser2',
                 'lstchg': 7, 'maxi': 9, 'warn': 10, 'flag': 13, 'gid': 1001, 'gecos': 'Testuser2', 'expire': 12,
                 'inact': 11, 'password': 'EFGH', 'uid': 1001}
    testuser3 = {'username': 'testuser3', 'mini': 15, 'shell': '/bin/zsh', 'homedir': '/home/testuser3',
                 'lstchg': 14, 'maxi': 16, 'warn': 17, 'flag': 20, 'gid': 1000, 'gecos': 'Testuser3',
                 'expire': 19, 'inact': 18, 'password': 'EFGH', 'uid': 1001}

    @classmethod
    def setUpClass(cls):
        ManagerTests.setUpClass()
        cls.um = UserManager(cls.config, cls.dbs)

    def test_adduser(self):
        self.um.adduser(**self.testuser)

    def test_getuserbyuid(self):
        self.um.adduser(**self.testuser)

        user = self.um.getuserbyuid(self.testuser['uid'])
        self.assertIsNotNone(user)

        del user['id']
        self.assertDictEqual(user, self.testuser)

        with self.assertRaises(KeyError):
            self.um.getuserbyuid(self.testuser2['uid'])

    def test_getuserbyusername(self):
        self.um.adduser(**self.testuser)
        user = self.um.getuserbyusername(self.testuser['username'])
        self.assertIsNotNone(user)

        del user['id']
        self.assertDictEqual(user, self.testuser)

        with self.assertRaises(KeyError):
            self.um.getuserbyusername(self.testuser2['username'])

    def test_deluser(self):
        self.um.adduser(**self.testuser)
        self.um.adduser(**self.testuser2)

        self.um.deluser(self.testuser['username'])
        with self.assertRaises(KeyError):
            self.um.getuserbyusername(self.testuser['username'])

        with self.assertRaises(KeyError):
            self.um.getuserbyuid(self.testuser['uid'])

        user = self.um.getuserbyusername(self.testuser2['username'])
        del user['id']
        self.assertEqual(user, self.testuser2)

    def test_moduser(self):
        self.um.adduser(**self.testuser)

        self.um.moduser(username_old=self.testuser['username'], **self.testuser2)

        user = self.um.getuserbyusername(self.testuser2['username'])
        del user['id']
        self.assertEqual(user, self.testuser2)

        with self.assertRaises(KeyError):
            self.um.getuserbyusername(self.testuser['username'])

        with self.assertRaises(KeyError):
            self.um.getuserbyuid(self.testuser['uid'])

    def test_modallgid(self):
        self.um.adduser(**self.testuser)
        self.um.adduser(**self.testuser3)

        self.um.modallgid(self.testuser['gid'], self.testuser2['gid'])

        user = self.um.getuserbyusername(self.testuser['username'])
        del user['id']
        self.assertEqual(user['gid'], self.testuser2['gid'])

        user = self.um.getuserbyusername(self.testuser3['username'])
        del user['id']
        self.assertEqual(user['gid'], self.testuser2['gid'])


class GroupManagerTests(ManagerTests):
    testgroup = {'name': 'testgroup', 'gid': 1000, 'password': 'ABCD'}
    testgroup2 = {'name': 'testgroup2', 'gid': 1001, 'password': 'EFGH'}

    @classmethod
    def setUpClass(cls):
        ManagerTests.setUpClass()
        cls.gm = GroupManager(cls.config, cls.dbs)

    def test_groupadd(self):
        self.gm.addgroup(**self.testgroup)

    def test_getgroupbygid(self):
        self.gm.addgroup(**self.testgroup)
        group = self.gm.getgroupbygid(self.testgroup['gid'])

        del group['id']

        self.assertDictEqual(group, self.testgroup)

        with self.assertRaises(KeyError):
            self.gm.getgroupbygid(self.testgroup2['gid'])

    def test_getgroupbyname(self):
        self.gm.addgroup(**self.testgroup)
        group = self.gm.getgroupbyname(self.testgroup['name'])

        del group['id']

        self.assertDictEqual(group, self.testgroup)

        with self.assertRaises(KeyError):
            self.gm.getgroupbyname(self.testgroup2['name'])

    def test_delgroup(self):
        self.gm.addgroup(**self.testgroup)
        self.gm.addgroup(**self.testgroup2)

        self.gm.delgroup(self.testgroup['gid'])

        with self.assertRaises(KeyError):
            self.gm.getgroupbygid(self.testgroup['gid'])

        with self.assertRaises(KeyError):
            self.gm.getgroupbyname(self.testgroup['name'])

        group = self.gm.getgroupbygid(self.testgroup2['gid'])
        del group['id']
        self.assertDictEqual(group, self.testgroup2)

    def test_modgroup(self):
        self.gm.addgroup(**self.testgroup)

        self.gm.modgroup(self.testgroup['name'], **self.testgroup2)

        with self.assertRaises(KeyError):
            self.gm.getgroupbygid(self.testgroup['gid'])

        with self.assertRaises(KeyError):
            self.gm.getgroupbyname(self.testgroup['name'])

        group = self.gm.getgroupbygid(self.testgroup2['gid'])
        del group['id']
        self.assertDictEqual(group, self.testgroup2)

        group = self.gm.getgroupbyname(self.testgroup2['name'])
        del group['id']
        self.assertDictEqual(group, self.testgroup2)


class GroupListManagerTests(ManagerTests):
    testgrouplist = {'username': 'testuser', 'gid': 1000}
    testgrouplist2 = {'username': 'testuser', 'gid': 1001}
    testgrouplist3 = {'username': 'testuser2', 'gid': 1000}

    @classmethod
    def setUpClass(cls):
        ManagerTests.setUpClass()
        cls.glm = GroupListManager(cls.config, cls.dbs)

    def test_addgroupuser(self):
        self.glm.addgroupuser(**self.testgrouplist)

    def test_getgroupsforuser(self):
        self.glm.addgroupuser(**self.testgrouplist)

        groups = self.glm.getgroupsforusername(self.testgrouplist['username'])

        self.assertListEqual(groups, [1000])

        with self.assertRaises(KeyError):
            self.glm.getgroupsforusername(self.testgrouplist3['username'])

    def test_delgroupuser(self):
        self.glm.addgroupuser(**self.testgrouplist)

        self.glm.delgroupuser(**self.testgrouplist)

        with self.assertRaises(KeyError):
            self.glm.getgroupsforusername(self.testgrouplist['username'])

    def test_delallgroupuser(self):
        self.glm.addgroupuser(**self.testgrouplist)
        self.glm.addgroupuser(**self.testgrouplist2)
        self.glm.addgroupuser(**self.testgrouplist3)

        self.glm.delallgroupuser(self.testgrouplist['username'])

        with self.assertRaises(KeyError):
            self.glm.getgroupsforusername(self.testgrouplist['username'])

        groups = self.glm.getgroupsforusername(self.testgrouplist3['username'])
        self.assertListEqual(groups, [self.testgrouplist3['gid']])

    def test_modallgroupuser(self):
        self.glm.addgroupuser(**self.testgrouplist)
        self.glm.addgroupuser(**self.testgrouplist2)

        self.glm.modallgroupuser(self.testgrouplist['username'], self.testgrouplist3['username'])

        with self.assertRaises(KeyError):
            self.glm.getgroupsforusername(self.testgrouplist['username'])

        groups = self.glm.getgroupsforusername(self.testgrouplist3['username'])
        self.assertListEqual(groups, [self.testgrouplist['gid'], self.testgrouplist2['gid']])

    def test_modallgroupgid(self):
        self.glm.addgroupuser(**self.testgrouplist)
        self.glm.addgroupuser(**self.testgrouplist3)

        self.glm.modallgroupgid(self.testgrouplist['gid'], self.testgrouplist2['gid'])

        self.assertNotIn(self.testgrouplist['gid'],
                         self.glm.getgroupsforusername(self.testgrouplist['username']))

        self.assertNotIn(self.testgrouplist3['gid'],
                         self.glm.getgroupsforusername(self.testgrouplist3['username']))


if __name__ == '__main__':
    unittest.main()
