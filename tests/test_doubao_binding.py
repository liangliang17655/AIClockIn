import tempfile
from pathlib import Path
import unittest
from aiclockin.store import Store
from aiclockin import doubao_binding as binding


class Backend:
    def __init__(self, fingerprint='a' * 64):
        self.fingerprint = fingerprint
        self.navigation_calls = 0
    def desktop_status(self): return True, 0
    def running(self): return True
    def inspect_identity(self): return {'account_fingerprint': self.fingerprint}
    def inspect(self, timeout):
        self.navigation_calls += 1
        return {'activity_ready': True, 'claim_button_count': 0}
    def inspect_ledger(self): return {'header_verified': False, 'dialog_closed': True, 'rows': []}


class BindingTests(unittest.TestCase):
    def setUp(self):
        root = Path('D:/个人开发软件/AI工作区/temp/AIClockIn-tests')
        root.mkdir(parents=True, exist_ok=True)
        folder = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(folder.cleanup)
        self.store = Store(folder.name)

    def test_confirmation_is_required(self):
        with self.assertRaises(ValueError): binding.confirm(self.store, 'a'*64, Backend())
        self.assertIsNone(binding.load(self.store))

    def test_identity_is_reread_before_save(self):
        with self.assertRaises(ValueError):
            binding.confirm(self.store, 'a'*64, Backend('b'*64), confirmed=True)
        self.assertIsNone(binding.load(self.store))

    def test_persisted_user_binding_is_not_verified_uid(self):
        saved = binding.confirm(self.store, 'a'*64, Backend(), confirmed=True)
        self.assertEqual(saved, binding.load(self.store))
        self.assertEqual(saved['mode'], 'user_confirmed_visible_number')
        self.assertFalse(saved['identity_verified'])
        self.assertNotIn('a'*64, (self.store.root/'doubao-binding.json').read_text('utf-8'))

    def test_missing_identity_stops(self):
        with self.assertRaises(ValueError):
            binding.confirm(self.store, 'a'*64, Backend(None), confirmed=True)
        self.assertIsNone(binding.load(self.store))

    def test_existing_binding_is_not_silently_replaced(self):
        old = binding.confirm(self.store, 'a'*64, Backend(), confirmed=True)
        with self.assertRaises(ValueError):
            binding.confirm(self.store, 'b'*64, Backend('b'*64), confirmed=True)
        self.assertEqual(old, binding.load(self.store))

    def test_bad_file_is_not_overwritten(self):
        file = self.store.root/'doubao-binding.json'; file.write_text('{}',encoding='utf-8')
        with self.assertRaises(ValueError):
            binding.confirm(self.store, 'a'*64, Backend(), confirmed=True)
        self.assertEqual(file.read_text('utf-8'), '{}')

    def test_unbound_worker_stops_before_navigation(self):
        from aiclockin.doubao_session import check_bound_session
        backend = Backend()
        result = check_bound_session(self.store, backend)
        self.assertEqual(result['reason'], 'binding_required')
        self.assertEqual(backend.navigation_calls, 0)

    def test_mismatch_stops_before_navigation_and_does_not_merge_history(self):
        from aiclockin.doubao_session import check_bound_session
        saved = binding.confirm(self.store, 'a'*64, Backend(), confirmed=True)
        backend = Backend('b'*64)
        result = check_bound_session(self.store, backend)
        self.assertEqual(result['reason'], 'account_mismatch')
        self.assertEqual(backend.navigation_calls, 0)
        self.assertNotEqual(self.store.history()[0]['account_id'], saved['id'])

    def test_matched_identity_is_not_daily_checkin_success(self):
        from aiclockin.doubao_session import check_bound_session
        saved = binding.confirm(self.store, 'a'*64, Backend(), confirmed=True)
        result = check_bound_session(self.store, Backend())
        self.assertEqual(result['reason'], 'daily_state_unknown')
        self.assertFalse(result['ready']); self.assertFalse(result['claim_attempted'])
        self.assertEqual(self.store.history()[0]['account_id'], saved['id'])
        self.assertIsNone(self.store.history()[0]['earned'])

    def test_identity_change_after_navigation_stops(self):
        from aiclockin.doubao_session import check_bound_session
        saved = binding.confirm(self.store, 'a'*64, Backend(), confirmed=True)
        backend = Backend()
        def navigate(timeout):
            backend.fingerprint = 'b'*64
            return {'activity_ready': True}
        backend.inspect = navigate
        result = check_bound_session(self.store, backend)
        self.assertEqual(result['reason'], 'account_mismatch_after_query')
        self.assertNotEqual(self.store.history()[0]['account_id'], saved['id'])

    def test_official_receipt_is_a_query_not_newly_earned_credit(self):
        from aiclockin.doubao_session import check_bound_session
        from datetime import datetime, timezone, timedelta
        binding.confirm(self.store, 'a'*64, Backend(), confirmed=True)
        backend = Backend()
        day = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
        backend.inspect_ledger = lambda: {'header_verified': True, 'dialog_closed': True,
            'rows': [{'task':'每日签到','time':day+' 00:23','earned':200}]}
        result = check_bound_session(self.store, backend)
        self.assertEqual(result['checkin_state'], 'already_signed')
        self.assertFalse(result['claim_attempted'])
        self.assertIsNone(self.store.history()[0]['earned'])

    def test_binding_confirmation_respects_operation_lock(self):
        from aiclockin.store import OperationLock, Busy
        with OperationLock(self.store.root):
            with self.assertRaises(Busy):
                binding.confirm(self.store, 'a'*64, Backend(), confirmed=True)
        self.assertIsNone(binding.load(self.store))

    def test_contradictory_claim_button_keeps_state_unknown(self):
        from aiclockin.doubao_session import check_bound_session
        from datetime import datetime, timezone, timedelta
        binding.confirm(self.store, 'a'*64, Backend(), confirmed=True)
        backend = Backend()
        day = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
        backend.inspect_ledger = lambda: {'header_verified': True, 'dialog_closed': True,
            'rows': [{'task':'每日签到','time':day+' 00:23','earned':200}]}
        backend.inspect = lambda timeout: {'activity_ready': True, 'claim_button_count': 1}
        result = check_bound_session(self.store, backend)
        self.assertEqual(result['checkin_state'], 'unknown')
        self.assertFalse(result['claim_attempted'])

    def test_lock_during_final_navigation_stops_record_association(self):
        from aiclockin.doubao_session import check_bound_session
        saved = binding.confirm(self.store, 'a'*64, Backend(), confirmed=True)
        backend = Backend(); original = backend.inspect
        def navigate(timeout):
            page = original(timeout)
            if backend.navigation_calls == 2:
                backend.desktop_status = lambda: (False, 5)
            return page
        backend.inspect = navigate
        result = check_bound_session(self.store, backend)
        self.assertEqual(result['reason'], 'desktop_unavailable')
        self.assertFalse(result['query_completed'])
        self.assertNotEqual(self.store.history()[0]['account_id'], saved['id'])
