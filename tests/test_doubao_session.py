from pathlib import Path
import tempfile
import unittest
from aiclockin import doubao_session as ds
from aiclockin.store import Store


class Fake:
    def __init__(self, running=True):
        self.active = running
        self.launches = 0
        self.desktop = True
        self.payload = {'running': True, 'activity_ready': True, 'account_fingerprint': 'a' * 64,
                        'claim_button_count': 0, 'cumulative': 400, 'steps': ['activity_menu']}
    def desktop_status(self): return self.desktop, 5 if not self.desktop else 0
    def running(self): return self.active
    def locate(self): return Path('D:/official/DoubaoWork.exe')
    def launch(self, exe): self.launches += 1; self.active = True
    def inspect(self, timeout): return self.payload


class SessionTests(unittest.TestCase):
    def setUp(self):
        root = Path('D:/个人开发软件/AI工作区/temp/AIClockIn-tests'); root.mkdir(parents=True, exist_ok=True)
        self.folder = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.folder.cleanup)
        self.store = Store(self.folder.name)

    def test_running_client_is_not_relaunched_and_preparation_is_not_claim(self):
        backend = Fake()
        result = ds.prepare_session(self.store, backend)
        self.assertEqual(backend.launches, 0)
        self.assertTrue(result['ready'])
        self.assertFalse(result['claim_attempted'])
        self.assertEqual(result['checkin_state'], 'unknown')
        row = self.store.history()[0]
        self.assertNotIn(row['state'], ('成功', '已签到'))
        self.assertIsNone(row['earned']); self.assertIsNone(row['balance'])

    def test_closed_client_launches_once(self):
        backend = Fake(False)
        result = ds.prepare_session(self.store, backend)
        self.assertEqual(backend.launches, 1)
        self.assertTrue(result['launch_started'])

    def test_locked_desktop_does_not_start_client(self):
        backend = Fake(False); backend.desktop = False
        result = ds.prepare_session(self.store, backend)
        self.assertEqual(backend.launches, 0)
        self.assertFalse(result['ready'])
        self.assertEqual(result['reason'], 'desktop_unavailable')

    def test_account_mismatch_never_claims_or_merges_history(self):
        result = ds.prepare_session(self.store, Fake(), expected_fingerprint='b' * 64)
        self.assertEqual(result['reason'], 'account_mismatch')
        self.assertFalse(result['ready']); self.assertFalse(result['claim_attempted'])

    def test_absent_identity_is_not_login_expired(self):
        backend = Fake(); backend.payload['account_fingerprint'] = None
        result = ds.prepare_session(self.store, backend)
        self.assertEqual(result['reason'], 'identity_unknown')
        self.assertNotIn('登录失效', self.store.history()[0]['detail'])

    def test_login_requirement_is_only_reported_when_explicit(self):
        backend = Fake(); backend.payload = {'running': True, 'login_required': True}
        result = ds.prepare_session(self.store, backend)
        self.assertEqual(result['reason'], 'login_required')

    def test_launch_failure_is_recorded_without_exception_content(self):
        backend = Fake(False)
        def fail(exe): raise OSError('private-token')
        backend.launch = fail
        result = ds.prepare_session(self.store, backend)
        self.assertEqual(result['reason'], 'launch_failed')
        self.assertNotIn('private-token', self.store.history()[0]['detail'])

    def test_missing_activity_preserves_navigation_failure(self):
        backend = Fake(); backend.payload = {'reason': 'activity_menu_missing'}
        result = ds.prepare_session(self.store, backend)
        self.assertEqual(result['reason'], 'activity_menu_missing')
        self.assertFalse(result['ready'])

    def test_timeout_does_not_create_success_or_amounts(self):
        import subprocess
        backend = Fake()
        def timeout(timeout): raise subprocess.TimeoutExpired('powershell', timeout)
        backend.inspect = timeout
        result = ds.prepare_session(self.store, backend)
        self.assertEqual(result['reason'], 'inspection_timeout')
        self.assertIsNone(self.store.history()[0]['earned'])

    def test_candidate_number_does_not_become_verified_identity(self):
        result = ds.prepare_session(self.store, Fake(), expected_fingerprint='a' * 64)
        self.assertEqual(result['identity_binding'], 'unverified')
        self.assertFalse(result['claim_attempted'])

    def test_bound_number_missing_stops_instead_of_using_cached_number(self):
        backend = Fake(); backend.payload['account_fingerprint'] = None
        result = ds.prepare_session(self.store, backend, expected_fingerprint='a' * 64)
        self.assertEqual(result['reason'], 'identity_unknown')
        self.assertFalse(result['ready'])


if __name__ == '__main__':
    unittest.main()
