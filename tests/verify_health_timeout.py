"""Build tests/fixtures/update_hang.py as a onefile EXE before explicitly running this test."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aiclockin.runtime import prepare
from aiclockin import update_apply as a
from aiclockin.update import file_hash
from aiclockin.store import Store, write_json


def main():
    prepare()
    base = Path(__file__).resolve().parent.parent
    new = base / 'dist/release/v0.2.0/AIClockIn-v0.2.0-windows-x64.exe'
    hanging = Path('D:/个人开发软件/AI工作区/temp/AIClockIn-hang-test/dist/AIClockIn.exe')
    with tempfile.TemporaryDirectory(prefix='frozen-health-timeout-') as folder:
        folder = Path(folder); target = folder / 'AIClockIn.exe'
        shutil.copyfile(new, target)
        data = folder / 'data'; Store(data).save_accounts([])
        before = file_hash(target)
        manifest = a.create_transaction(target, hanging, data, '0.2.0', file_hash(hanging))
        original = a.health_check
        with patch.object(a, 'health_check', side_effect=lambda target, manifest, expected: original(target, manifest, expected, timeout=5)):
            try:
                a.replace_transaction(manifest)
                raise AssertionError('Hanging frozen self-test should time out')
            except a.ApplyError as exc:
                assert '超时' in str(exc), str(exc)
        assert a.load_manifest(manifest)['state'] == 'restored'
        assert file_hash(target) == before
        child_file = manifest.parent / 'health.child-pid'
        assert child_file.exists(), 'Nested frozen Python process never started'
        pid = int(child_file.read_text('ascii'))
        api = a.kernel(); handle = api.OpenProcess(0x100000, False, pid)
        if handle:
            try:
                assert api.WaitForSingleObject(handle, 1000) == 0, 'Nested frozen child survived'
            finally:
                api.CloseHandle(handle)
        report = {'frozen_nested_timeout': True, 'child_exited': True, 'rollback': True,
                  'original_hash': before, 'transaction': str(manifest)}
        output = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/update/frozen-timeout.json')
        write_json(output, report)
        print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
