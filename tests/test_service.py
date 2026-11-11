import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from aiclockin.store import Store
try:
    from aiclockin.service import Service
except ImportError:
    Service = None


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Service)
        self.temp = tempfile.TemporaryDirectory(dir='D:/个人开发软件/AI工作区/temp/AIClockIn-tests')
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name))

    def test_one_failure_does_not_skip_next_account_or_leak_credentials(self):
        accounts = [{'id': i, 'platform': 'workbuddy', 'name': i.upper(), 'enabled': True,
                     'credentials': {'uid': 'user-' + i, 'access_token': 'private-' + i}} for i in ('a', 'b')]
        self.store.save_accounts(accounts)
        class Client:
            def post(self, url, headers, body):
                if headers['Authorization'] == 'Bearer private-a':
                    raise RuntimeError('timeout private-a')
                return {'code': 0, 'data': {'today_checked_in': True}}
        ok, message = Service(self.store, Client()).run(sync=False)
        self.assertFalse(ok)
        rows = self.store.history()
        self.assertEqual(len(rows), 2)
        self.assertEqual({r['state'] for r in rows}, {'失败', '已签到'})
        self.assertNotIn('private-a', repr(rows))
        self.assertEqual({r['account_id'] for r in rows}, {'a', 'b'})

    def test_relogin_keeps_local_identity_name_and_disabled_state(self):
        rows = [{'id': 'stable', 'platform': 'trae', 'name': '自定名称', 'enabled': False,
                 'credentials': {'userId': 'person', 'accessToken': 'old'}}]
        Service(self.store).merge(rows, 'trae', {'userId': 'person', 'accessToken': 'new'}, '新昵称')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['id'], 'stable')
        self.assertEqual(rows[0]['name'], '自定名称')
        self.assertFalse(rows[0]['enabled'])
        self.assertEqual(rows[0]['credentials']['accessToken'], 'new')

    def test_no_enabled_accounts_is_not_success(self):
        self.assertFalse(Service(self.store).run(sync=False)[0])


if __name__ == '__main__':
    unittest.main()
