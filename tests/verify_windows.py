"""Opt-in isolated Windows task and frozen-app verification. No real accounts."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aiclockin.runtime import prepare
from aiclockin.schedule import TaskManager, WindowsTask, powershell
from aiclockin.store import Store, write_json


def main():
    prepare()
    base = Path(__file__).resolve().parent.parent
    exe = base / 'AIClockIn.exe'
    output = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation')
    output.mkdir(parents=True, exist_ok=True)
    report = output / 'exe-selftest.json'
    report.unlink(missing_ok=True)
    result = subprocess.run([str(exe), '--self-test', '--report', str(report)], timeout=35)
    assert result.returncode == 0 and json.loads(report.read_text('utf-8'))['ok']
    task_name = 'AIClockIn-Test-' + uuid.uuid4().hex[:12]
    backend = WindowsTask(task_name)
    record = {'offline_selftest': True, 'task': False, 'cleanup': False,
              'sha256': hashlib.sha256(exe.read_bytes()).hexdigest(), 'size_bytes': exe.stat().st_size}
    with tempfile.TemporaryDirectory(prefix='windows-test-') as directory:
        folder = Path(directory)
        target = folder / 'AIClockIn.exe'
        shutil.copy2(exe, target)
        data = folder / 'custom data'
        Store(data).save_accounts([])
        manager = TaskManager(data, target, backend)
        try:
            manager.enable()
            assert manager.status()['enabled']
            powershell(f"Start-ScheduledTask -TaskName '{task_name}' -TaskPath '\\'")
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                raw = powershell(f"$t=Get-ScheduledTask -TaskName '{task_name}';$i=Get-ScheduledTaskInfo -TaskName '{task_name}';@{{State=[string]$t.State;Result=$i.LastTaskResult;Ran=($i.LastRunTime.Year -gt 2020)}}|ConvertTo-Json -Compress")
                info = json.loads(raw)
                if info['Ran'] and info['State'] != 'Running':
                    break
                time.sleep(.5)
            assert info['Ran'] and info['State'] != 'Running' and info['Result'] == 1, info
            assert not (target.parent / 'data').exists(), 'Task ignored custom data directory'
            manager.disable()
            assert backend.get() is None
            record['task'] = True
            record['empty_accounts_exit'] = 1
        finally:
            if backend.get() is not None:
                backend.remove()
            record['cleanup'] = backend.get() is None
            write_json(output / 'windows.json', record)
    print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    main()
