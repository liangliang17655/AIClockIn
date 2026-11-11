from pathlib import Path
import tempfile
import unittest

try:
    from aiclockin.providers import WorkBuddy, Trae
    from aiclockin.store import Store, OperationLock, Busy
except ImportError:
    WorkBuddy = Trae = Store = None


class FakeHTTP:
    def __init__(self, handler):
        self.handler = handler
        self.calls = []

    def post(self, url, headers, body):
        self.calls.append(url)
        return self.handler(url, headers, body)


class PlatformTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(WorkBuddy, '独立平台模块未实现')
        self.wb = {'id': 'wb-a', 'name': '示例', 'platform': 'workbuddy', 'credentials': {'access_token': 'fake-token', 'uid': 'fake-uid'}}
        self.trae = {'id': 'tr-a', 'name': '示例', 'platform': 'trae', 'credentials': {'accessToken': 'fake-token', 'refreshToken': 'fake-refresh', 'userId': 'fake-user', 'claimDeviceId': 'actual-client-device'}}

    def test_workbuddy_checks_before_claim_and_verifies_after(self):
        steps = []
        def reply(url, headers, body):
            if url.endswith('checkin-activity-status'):
                steps.append('status')
                return {'code': 0, 'data': {'today_checked_in': len(steps) > 1, 'daily_credit': 100}}
            if url.endswith('daily-checkin'):
                steps.append('claim')
                self.assertEqual(headers['Authorization'], 'Bearer fake-token')
                return {'code': 0}
            return {'code': 0, 'data': {}}
        http = FakeHTTP(reply)
        result = WorkBuddy(http).run(self.wb)
        self.assertEqual(steps, ['status', 'claim', 'status'])
        self.assertEqual(result.state, '成功')
        self.assertEqual(result.earned, 100)
        self.assertIsNone(result.balance)
        self.assertIn('余额未获取', result.detail)

    def test_already_signed_never_claims_or_reports_new_earnings(self):
        http = FakeHTTP(lambda *args: {'code': 0, 'data': {'today_checked_in': True, 'daily_credit': 100}})
        result = WorkBuddy(http).run(self.wb)
        self.assertEqual(result.state, '已签到')
        self.assertIsNone(result.earned)
        self.assertFalse(any(url.endswith('daily-checkin') for url in http.calls))

    def test_unconfirmed_claim_is_failure(self):
        http = FakeHTTP(lambda *args: {'code': 0, 'data': {'today_checked_in': False}})
        self.assertEqual(WorkBuddy(http).run(self.wb).state, '失败')

    def test_trae_device_denial_does_not_verify_or_retry(self):
        def reply(url, *args):
            if url.endswith('/claim'):
                return {'code': 9095, 'message': '当前设备今日已经签到，请明日再来哦～'}
            if url.endswith('/status'):
                return {'code': 0, 'data': {'checked_in': False}}
            return {'code': 0, 'data': {}}
        http = FakeHTTP(reply)
        result = Trae(http).run(self.trae)
        self.assertEqual(result.state, '设备受限')
        self.assertIn('9095', result.detail)
        self.assertEqual(sum(u.endswith('/claim') for u in http.calls), 1)
        self.assertEqual(sum(u.endswith('/status') for u in http.calls), 1)

    def test_trae_uses_actual_gain(self):
        state = {'claimed': False}
        def reply(url, headers, body):
            self.assertEqual(headers.get('x-device-id'), 'actual-client-device')
            if url.endswith('/status'):
                return {'code': 0, 'data': {'checked_in': state['claimed']}}
            if url.endswith('/claim'):
                state['claimed'] = True
                return {'code': 0, 'data': {'credits': 200}}
            return {'code': 0, 'data': {'usage_summary': {'total_amount': 350 if state['claimed'] else 200, 'consumed_amount': 100}}}
        result = Trae(FakeHTTP(reply)).run(self.trae)
        self.assertEqual(result.state, '成功')
        self.assertEqual(result.earned, 150)
        self.assertEqual(result.balance, 250)

    def test_status_business_error_is_not_unsigned_success(self):
        http = FakeHTTP(lambda *args: {'code': 1001, 'message': '认证失败'})
        result = Trae(http).run(self.trae, status_only=True)
        self.assertEqual(result.state, '失败')

    def test_unknown_status_does_not_trigger_claim(self):
        for provider, account in [(WorkBuddy, self.wb), (Trae, self.trae)]:
            http = FakeHTTP(lambda *args: {'code': 0, 'data': {}})
            result = provider(http).run(account)
            self.assertEqual(result.state, '失败')
            self.assertFalse(any(url.endswith(('/claim', '/daily-checkin')) for url in http.calls))


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Store, '独立存储未实现')
        base = Path('D:/个人开发软件/AI工作区/temp/AIClockIn-tests')
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name))

    def test_encryption_and_account_independence(self):
        data = [{'id': 'a', 'name': 'A', 'platform': 'workbuddy', 'enabled': True, 'credentials': {'uid': 'u-a', 'access_token': 'private-a'}},
                {'id': 'b', 'name': 'B', 'platform': 'trae', 'enabled': False, 'credentials': {'userId': 'u-b', 'accessToken': 'private-b'}}]
        self.store.save_accounts(data)
        raw = self.store.account_file.read_bytes()
        self.assertNotIn(b'private-a', raw)
        self.assertNotIn(b'private-b', raw)
        loaded = self.store.accounts()
        self.assertEqual(loaded, data)
        loaded[0]['credentials']['access_token'] = 'updated'
        self.store.save_accounts(loaded)
        self.assertEqual(self.store.accounts()[1]['credentials']['accessToken'], 'private-b')

    def test_corrupt_config_not_overwritten(self):
        self.store.account_file.write_text('broken', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.store.save_accounts([])
        self.assertEqual(self.store.account_file.read_text('utf-8'), 'broken')

    def test_history_survives_restart_with_unknown_values(self):
        self.store.record('a', 'workbuddy', 'A', '失败', None, None, '接口超时')
        row = Store(Path(self.temp.name)).history()[0]
        self.assertEqual(row['state'], '失败')
        self.assertIsNone(row['balance'])
        self.assertEqual(row['account_id'], 'a')

    def test_operation_lock_is_exclusive_and_released(self):
        with OperationLock(self.store.root):
            with self.assertRaises(Busy):
                with OperationLock(self.store.root):
                    self.fail('must not acquire twice')
        with OperationLock(self.store.root):
            pass


if __name__ == '__main__':
    unittest.main()
