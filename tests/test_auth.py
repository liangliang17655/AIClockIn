import base64
import json
from pathlib import Path
import tempfile
import unittest
from aiclockin.workbuddy_auth import WbAuthSnapshot


class AuthTests(unittest.TestCase):
    def test_mismatched_snapshot_owner_never_binds_another_accounts_token(self):
        token = 'header.' + base64.urlsafe_b64encode(json.dumps({'sub': 'account-A'}).encode()).decode().rstrip('=') + '.signature'
        with tempfile.TemporaryDirectory(dir='D:/个人开发软件/AI工作区/temp/AIClockIn-tests') as folder:
            path = Path(folder) / 'test.info'
            path.write_text(json.dumps({'auth': {'accessToken': token}, 'account': {'uid': 'account-B', 'nickname': 'B'}}), 'utf-8')
            snapshot = WbAuthSnapshot(path, quiet=True)
            self.assertFalse(snapshot.load())
            self.assertIsNone(snapshot.record)
