from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aiclockin import installer as i
from aiclockin.runtime import TEMP
from aiclockin.store import Store
from aiclockin.update import file_hash


class InstallerTests(unittest.TestCase):
    def setUp(self):
        TEMP.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=TEMP)
        self.folder = Path(self.tmp.name)
        self.source = self.folder / 'download' / 'AIClockIn.exe'
        self.source.parent.mkdir(); self.source.write_bytes(b'new exe')

    def tearDown(self):
        self.tmp.cleanup()

    def test_bootstrap_only_for_unconfigured_frozen_gui(self):
        self.assertTrue(i.needs_install(self.source, frozen=True, gui=True))
        for kwargs in ({'frozen': False, 'gui': True}, {'frozen': True, 'gui': False},
                       {'frozen': True, 'gui': True, 'data': self.folder/'custom'}):
            self.assertFalse(i.needs_install(self.source, **kwargs))
        (self.source.parent / 'data').mkdir()
        (self.source.parent / 'data' / 'accounts.json').write_text('do not read')
        self.assertFalse(i.needs_install(self.source, frozen=True, gui=True))

    def test_default_and_existing_location_no_migration(self):
        default = self.folder / 'fresh-default'
        with patch.object(i, 'DEFAULT', default):
            self.assertEqual(i.location(self.source, task=None), (default, default/'data', False))
        data = self.folder / 'private data'; Store(data).save_accounts([])
        self.assertEqual(i.location(self.source, data=data), (self.source.parent, data, True))

    def test_existing_default_install_without_auto_task_is_preserved(self):
        default = self.folder / 'default install'
        (default/'data').mkdir(parents=True)
        (default/'data/accounts.json').write_text('must not read or migrate')
        with patch.object(i, 'DEFAULT', default):
            self.assertEqual(i.location(self.source, task=None), (default, default/'data', True))

    def test_competing_shortcuts_never_overwrite_each_other(self):
        import gc
        gc.collect()  # Dispose earlier destroyed Tk fixtures on their owning thread before starting workers.
        import concurrent.futures
        desk = self.folder / 'desktop'; desk.mkdir()
        barrier = self.folder / 'barrier'; barrier.mkdir()
        original_shell = i.shell
        def synchronized_shell(script, value):
            if '$temp=Join-Path' in script:
                script = script.replace('$temp=Join-Path', r'''$marker=Join-Path $v.barrier ([Guid]::NewGuid().ToString('N'));
                    [IO.File]::WriteAllText($marker,'ready');$until=[DateTime]::UtcNow.AddSeconds(8);
                    while((Get-ChildItem -LiteralPath $v.barrier).Count -lt 2){
                        if([DateTime]::UtcNow -gt $until){throw 'Barrier timeout'};Start-Sleep -Milliseconds 20};
                    $temp=Join-Path''')
                value['barrier'] = str(barrier)
            return original_shell(script, value)
        def create(index):
            try:
                i.create_shortcut(self.folder / str(index) / 'AIClockIn.exe', self.folder / str(index) / 'data', desk)
                return True
            except i.InstallError:
                return False
        with patch.object(i, 'shell', side_effect=synchronized_shell), concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, (1, 2)))
        self.assertEqual(sum(results), 1)

    def test_task_location_preserves_custom_data(self):
        from aiclockin.schedule import definition
        exe = self.folder / 'installed' / 'AIClockIn.exe'; exe.parent.mkdir(); exe.write_bytes(b'existing')
        data = self.folder / 'custom data'
        backend = unittest.mock.Mock()
        backend.user = 'S-1-5-21-synthetic'
        backend.get.return_value = definition(exe, backend.user, data)
        self.assertEqual(i.location(self.source, task=backend), (exe.parent, data, True))

    def test_destination_d_only_and_not_data_folder(self):
        with self.assertRaises(i.InstallError):
            i.destination(Path('C:/Users/test/Desktop'))
        self.assertEqual(i.destination(self.folder), self.folder.resolve() / 'AIClockIn.exe')

    def test_new_install_preserves_data_and_shortcut_parameters(self):
        target = self.folder / 'installed'; data = target / 'data'
        Store(data).save_accounts([])
        before = {p.name: file_hash(p) for p in data.iterdir()}
        with patch.object(i, 'health_check', return_value=True), patch.object(i, 'validate_pe'), \
             patch.object(i, 'create_shortcut', return_value='desktop link') as shortcut:
            result = i.install(self.source, target, data, '0.3.0')
        self.assertEqual(result, target / 'AIClockIn.exe')
        self.assertEqual(result.read_bytes(), b'new exe')
        shortcut.assert_called_once_with(result, data, desktop=None)
        self.assertEqual(before, {p.name: file_hash(p) for p in data.iterdir() if p.name != 'operation.lock'})

    def test_failed_health_never_creates_target(self):
        target = self.folder / 'installed'
        with patch.object(i, 'health_check', side_effect=RuntimeError('bad exe')), patch.object(i, 'validate_pe'), \
             patch.object(i, 'create_shortcut') as shortcut:
            with self.assertRaises(i.InstallError):
                i.install(self.source, target, target/'data', '0.3.0')
        self.assertFalse((target/'AIClockIn.exe').exists())
        shortcut.assert_not_called()

    def test_same_exe_only_creates_link_and_link_failure_not_success(self):
        data = self.source.parent / 'data'
        with patch.object(i, 'create_shortcut', side_effect=RuntimeError('link denied')), patch.object(i, 'validate_pe'):
            with self.assertRaisesRegex(i.InstallError, '快捷方式'):
                i.install(self.source, self.source.parent, data, '0.3.0')
        self.assertEqual(self.source.read_bytes(), b'new exe')


if __name__ == '__main__':
    unittest.main()
