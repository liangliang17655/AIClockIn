"""Opt-in actual scheduled execution of current folder build with disabled fixtures."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aiclockin.package import copy_bundle
from aiclockin.runtime import prepare
from aiclockin.schedule import WindowsTask, TaskManager, powershell
from aiclockin.store import Store, write_json
from aiclockin.update import file_hash


def main():
    prepare()
    base = Path(__file__).resolve().parents[1]
    version = (base / 'VERSION').read_text('utf-8').strip()
    output = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork')
    original = WindowsTask().get()
    task = WindowsTask('AIClockIn-ReleaseCheck-' + uuid.uuid4().hex[:12])
    with tempfile.TemporaryDirectory(prefix='release-task-') as folder:
        folder = Path(folder)
        bundle = folder / 'app'
        copy_bundle(base / f'dist/bundle/v{version}/AIClockIn', bundle)
        data = folder / 'private data'
        store = Store(data)
        rows = [{'id': 'offline', 'platform': 'workbuddy', 'name': 'disabled fixture', 'enabled': False,
                 'credentials': {'uid': 'synthetic', 'access_token': 'synthetic'}}]
        store.save_accounts(rows)
        store.record('offline', 'workbuddy', 'disabled fixture', '失败', None, None, 'isolated offline fixture')
        manager = TaskManager(data, bundle / 'AIClockIn.exe', task)
        result = {'version': version, 'real_platform_signin': False}
        try:
            manager.enable()
            assert manager.status()['enabled']
            xml = task.get()
            before = {p.name: file_hash(p) for p in data.iterdir() if p.is_file()}
            powershell(f"Start-ScheduledTask -TaskName '{task.name}' -TaskPath '\\'")
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                info = json.loads(powershell(f"$t=Get-ScheduledTask -TaskName '{task.name}';$i=Get-ScheduledTaskInfo -TaskName '{task.name}';@{{state=[string]$t.State;exit=$i.LastTaskResult;ran=($i.LastRunTime.Year -gt 2020)}}|ConvertTo-Json -Compress"))
                if info['ran'] and info['state'] != 'Running':
                    break
                time.sleep(.5)
            assert info['ran'] and info['state'] != 'Running' and info['exit'] == 1, info
            assert before == {p.name: file_hash(p) for p in data.iterdir() if p.is_file()}
            assert Store(data).accounts() == rows
            assert task.get() == xml
            assert not (bundle / 'data').exists()
            result.update({'scheduled_current_exe': True, 'truthful_no_enabled_accounts_exit': 1,
                           'data_hashes_preserved': True, 'task_xml_unchanged': True})
        finally:
            if task.get() is not None:
                task.remove()
            result['temporary_task_removed'] = task.get() is None
            result['production_task_unchanged'] = WindowsTask().get() == original
            write_json(output / f'task017-scheduled-{version}.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
