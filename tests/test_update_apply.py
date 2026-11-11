from pathlib import Path
import tempfile
import unittest
import sys
import time
from unittest.mock import patch

from aiclockin import update_apply as a
from aiclockin.update import file_hash, ROOT
from aiclockin.store import Store


class ApplyTests(unittest.TestCase):
    def setUp(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.folder = Path(self.tmp.name)
        self.target = self.folder / 'app' / 'AIClockIn.exe'
        self.target.parent.mkdir()
        self.target.write_bytes(b'original')
        self.candidate = self.folder / 'candidate.exe'
        self.candidate.write_bytes(b'candidate')
        self.data = self.target.parent / 'data'
        self.store = Store(self.data)
        self.store.save_accounts([{'id': 'a', 'name': 'test', 'platform': 'workbuddy', 'enabled': True,
                                  'credentials': {'uid': 'synthetic', 'access_token': 'synthetic-token'}}])
        self.store.record('a', 'workbuddy', 'test', '失败', None, None, '模拟超时')
        self.before = {p.name: p.read_bytes() for p in self.data.iterdir()}

    def tearDown(self):
        self.tmp.cleanup()

    def transaction(self):
        return a.create_transaction(self.target, self.candidate, self.data, '0.2.0', file_hash(self.candidate))

    def test_success_replaces_only_exe_and_retains_backup(self):
        manifest = self.transaction()
        with patch.object(a, 'health_check', return_value=True):
            a.replace_transaction(manifest)
        self.assertEqual(self.target.read_bytes(), b'candidate')
        self.assertEqual((manifest.parent / 'previous.exe').read_bytes(), b'original')
        self.assertEqual(self.before, {p.name: p.read_bytes() for p in self.data.iterdir()})
        self.assertEqual(self.store.accounts()[0]['credentials']['uid'], 'synthetic')

    def test_health_failure_restores_original_and_data(self):
        manifest = self.transaction()
        with patch.object(a, 'health_check', side_effect=RuntimeError('health failed')):
            with self.assertRaises(a.ApplyError):
                a.replace_transaction(manifest)
        self.assertEqual(self.target.read_bytes(), b'original')
        self.assertEqual(self.before, {p.name: p.read_bytes() for p in self.data.iterdir()})

    def test_tampered_candidate_never_replaces(self):
        manifest = self.transaction()
        Path(a.load_manifest(manifest)['candidate']).write_bytes(b'tampered')
        with self.assertRaises(a.ApplyError):
            a.replace_transaction(manifest)
        self.assertEqual(self.target.read_bytes(), b'original')

    def test_interrupted_replacement_recovery(self):
        manifest = self.transaction()
        value = a.load_manifest(manifest)
        (manifest.parent / 'previous.exe').write_bytes(b'original')
        self.target.write_bytes(b'candidate')
        value['state'] = 'replacing'
        a.save_manifest(manifest, value)
        a.recover(manifest)
        self.assertEqual(self.target.read_bytes(), b'original')

    def test_concurrent_application_gate(self):
        with a.UpdateGate(self.target, timeout=1):
            # Windows mutex is recursive on one thread, test another thread instead.
            import threading
            errors = []
            def attempt():
                try:
                    with a.UpdateGate(self.target, timeout=0.05):
                        pass
                except a.ApplyError:
                    errors.append(True)
            thread = threading.Thread(target=attempt); thread.start(); thread.join()
            self.assertEqual(errors, [True])

    def test_file_in_use_keeps_original_and_reports_failure(self):
        manifest = self.transaction()
        with patch.object(a, 'atomic_replace', side_effect=PermissionError('in use')):
            with self.assertRaises(a.ApplyError):
                a.replace_transaction(manifest)
        self.assertEqual(self.target.read_bytes(), b'original')
        self.assertEqual(a.load_manifest(manifest)['state'], 'failed')

    def test_rollback_failure_is_honest_and_keeps_backup(self):
        manifest = self.transaction()
        with patch.object(a, 'health_check', side_effect=RuntimeError('failed')), \
             patch.object(a, 'restore', side_effect=PermissionError('denied')):
            with self.assertRaisesRegex(a.ApplyError, '自动恢复未完成'):
                a.replace_transaction(manifest)
        self.assertEqual(a.load_manifest(manifest)['state'], 'restore-failed')
        self.assertEqual((manifest.parent / 'previous.exe').read_bytes(), b'original')
        a.recover(manifest)
        self.assertEqual(self.target.read_bytes(), b'original')

    def test_backup_is_flushed_before_replacing_state(self):
        manifest = self.transaction()
        events = []
        original_save = a.save_manifest
        def save(path, value):
            events.append(value['state'])
            original_save(path, value)
        with patch.object(a, 'durable_copy', side_effect=lambda source, target: (events.append(Path(target).name), a.shutil.copyfile(source, target))), \
             patch.object(a, 'save_manifest', side_effect=save), patch.object(a, 'health_check', return_value=True):
            a.replace_transaction(manifest)
        self.assertLess(events.index('previous.exe'), events.index('replacing'))

    def test_health_timeout_closes_entire_job(self):
        manifest = self.transaction()
        with patch.object(a, 'HealthProcess') as factory:
            process = factory.return_value.__enter__.return_value
            process.wait.side_effect = a.subprocess.TimeoutExpired('self-test', 90)
            with self.assertRaises(a.ApplyError):
                a.health_check(self.target, manifest, '0.2.0')
            factory.return_value.__exit__.assert_called_once()

    def test_real_job_kills_nested_python_processes(self):
        pid_file = self.folder / 'child-pid.txt'
        script = ('import subprocess,sys,time; from pathlib import Path; '
                  'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"]); '
                  f'Path({str(pid_file)!r}).write_text(str(p.pid)); time.sleep(60)')
        with a.HealthProcess([sys.executable, '-B', '-c', script], self.folder, a.child_env()) as process:
            deadline = time.monotonic() + 5
            while not pid_file.exists() and time.monotonic() < deadline:
                time.sleep(.05)
            self.assertTrue(pid_file.exists())
            pid = int(pid_file.read_text())
            api = a.kernel(); handle = api.OpenProcess(0x100000, False, pid)
            self.assertTrue(handle)
            with self.assertRaises(a.subprocess.TimeoutExpired):
                process.wait(.05)
        try:
            self.assertEqual(api.WaitForSingleObject(handle, 1000), 0)
        finally:
            api.CloseHandle(handle)

    def test_durable_copy_flushes_contents(self):
        backup = self.folder / 'copy.exe'
        with patch.object(a.os, 'fsync', wraps=a.os.fsync) as flushed:
            a.durable_copy(self.target, backup)
            flushed.assert_called_once()
        self.assertEqual(backup.read_bytes(), b'original')


if __name__ == '__main__':
    unittest.main()
