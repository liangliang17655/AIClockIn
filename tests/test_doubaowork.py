import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from aiclockin import doubaowork as dw
from aiclockin.store import Store


def payload(**changes):
    data = {'running': True, 'truncated': False, 'quota': [{'used': 0, 'total': 200,
            'expiry': '12月14日 19:05 到期'}], 'campaign': [{'cumulative': 200}]}
    data.update(changes)
    return data


class DoubaoTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(dw, 'desktop_status', return_value=(True, 0))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_actual_field_semantics_do_not_prove_daily_claim(self):
        result = dw.parse(payload())
        self.assertEqual((result.used, result.remaining, result.cumulative), (0, 200, None))
        self.assertIn('不合并', result.issue)
        self.assertIsNone(result.earned)
        self.assertIsNone(result.identity)
        self.assertEqual(result.checkin, '状态未知')

    def test_campaign_only_observation_has_cumulative_but_no_balance(self):
        result = dw.parse(payload(quota=[]))
        self.assertEqual(result.cumulative, 200)
        self.assertIsNone(result.remaining)

    def test_missing_fields_are_null_not_zero_or_cached(self):
        result = dw.parse(payload(quota=[], campaign=[]))
        self.assertIsNone(result.remaining)
        self.assertIsNone(result.cumulative)
        self.assertFalse(result.has_data)

    def test_conflicting_windows_fail_closed(self):
        result = dw.parse(payload(quota=[{'used': 0, 'total': 200, 'expiry': ''},
                                        {'used': 0, 'total': 100, 'expiry': ''}]))
        self.assertIsNone(result.remaining)
        self.assertIn('冲突', result.issue)
        self.assertIsNone(result.cumulative)

    def test_invalid_numbers_and_truncated_tree_are_rejected(self):
        for change in ({'quota': [{'used': 201, 'total': 200}]}, {'truncated': True}):
            with self.subTest(change=change):
                self.assertFalse(dw.parse(payload(**change)).has_data)

    def test_closed_client_has_explicit_error(self):
        result = dw.parse(payload(running=False))
        self.assertFalse(result.has_data)
        self.assertIn('未运行', result.issue)

    def test_timeout_does_not_leak_stdout_or_exception(self):
        with patch.object(dw.subprocess, 'run', side_effect=subprocess.TimeoutExpired('private-token', 1)):
            result = dw.query(timeout=1)
        self.assertIn('超时', result.issue)
        self.assertNotIn('private-token', repr(result))

    def test_process_error_never_logs_remote_or_private_text(self):
        completed = subprocess.CompletedProcess([], 1, 'private-cookie', 'private-token')
        with patch.object(dw.subprocess, 'run', return_value=completed):
            result = dw.query()
        self.assertNotIn('private-', repr(result))

    def test_non_json_output_is_unknown(self):
        with patch.object(dw.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'not-json', b'')):
            self.assertFalse(dw.query().has_data)

    def test_structured_uia_error_preserves_type_stage_and_hresult_only(self):
        result = dw.parse({'error': {'stage': 'traversal', 'type': 'System.Runtime.InteropServices.COMException',
                                   'hresult': -2147220991, 'message': 'private-token'}})
        self.assertFalse(result.has_data)
        self.assertIn('traversal', result.issue)
        self.assertIn('COMException', result.issue)
        self.assertIn('-2147220991', result.issue)
        self.assertNotIn('private-token', result.issue)

    def test_unavailable_desktop_never_reads_cached_page_or_reports_expired_login(self):
        with patch.object(dw, 'desktop_status', return_value=(False, 5)), patch.object(dw.subprocess, 'run') as run:
            result = dw.query()
        run.assert_not_called()
        self.assertFalse(result.has_data)
        self.assertIn('5', result.issue)
        self.assertEqual(result.state, '额度查询失败')
        self.assertIn('不判定登录失效', result.issue)

    def test_records_survive_reopen_without_identity_merging(self):
        root = Path('D:/个人开发软件/AI工作区/temp/AIClockIn-tests')
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temp:
            store = Store(temp)
            store.save_accounts([{'id': 'existing', 'platform': 'trae', 'name': 'existing',
                                  'credentials': {'accessToken': 'secret'}}])
            original_accounts = store.account_file.read_bytes()
            dw.record(store, dw.parse(payload()))
            dw.record(store, dw.parse(payload(quota=[], campaign=[{'cumulative': 300}])) )
            rows = Store(temp).history()
            self.assertEqual(len({row['account_id'] for row in rows}), 2)
            self.assertTrue(all(row['earned'] is None for row in rows))
            self.assertIsNone(rows[0]['balance'])
            detail = json.loads(rows[1]['detail'])
            self.assertEqual(detail['binding'], '账号身份待确认')
            self.assertEqual(detail['total'], 200)
            self.assertEqual(store.account_file.read_bytes(), original_accounts)

    def test_failure_record_does_not_copy_previous_balance(self):
        root = Path('D:/个人开发软件/AI工作区/temp/AIClockIn-tests')
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temp:
            store = Store(temp)
            dw.record(store, dw.parse(payload()))
            dw.record(store, dw.parse(payload(running=False)))
            row = store.history()[0]
            self.assertEqual(row['state'], '额度查询失败')
            self.assertIsNone(row['balance'])
            self.assertIsNone(row['earned'])


if __name__ == '__main__':
    unittest.main()
