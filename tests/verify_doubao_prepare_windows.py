"""Opt-in real scheduled preflight. Uses isolated data and never claims."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aiclockin.schedule import WindowsTask, powershell


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, help='Optional confirmed binding data; appends real query only, never claims')
    args = parser.parse_args()
    base = Path(__file__).resolve().parents[1]
    output = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/task025') / uuid.uuid4().hex[:12]
    output.mkdir(parents=True)
    report = output / 'report.json'
    task = WindowsTask('AIClockIn-DoubaoPrepare-' + uuid.uuid4().hex[:12])
    original = WindowsTask().get()
    ns = 'http://schemas.microsoft.com/windows/2004/02/mit/task'
    ET.register_namespace('', ns)
    root = ET.Element('{' + ns + '}Task', version='1.2')
    def node(parent, name, value=None):
        child = ET.SubElement(parent, '{' + ns + '}' + name)
        child.text = value
        return child
    principal = node(node(root, 'Principals'), 'Principal'); principal.set('id', 'Owner')
    node(principal, 'UserId', task.user)
    node(principal, 'LogonType', 'InteractiveToken')
    node(principal, 'RunLevel', 'LeastPrivilege')
    settings = node(root, 'Settings')
    node(settings, 'ExecutionTimeLimit', 'PT3M')
    node(settings, 'MultipleInstancesPolicy', 'IgnoreNew')
    node(settings, 'DisallowStartIfOnBatteries', 'false')
    node(settings, 'StopIfGoingOnBatteries', 'false')
    actions = node(root, 'Actions'); actions.set('Context', 'Owner')
    action = node(actions, 'Exec')
    node(action, 'Command', str(Path(sys.executable).resolve()))
    node(action, 'Arguments', subprocess.list2cmdline(['-B', str(base / 'main.py'),
         '--doubao-prepare', '--data', str(args.data.resolve() if args.data else output / 'data'), '--report', str(report)]))
    node(action, 'WorkingDirectory', str(base))
    result = {}
    try:
        task.put(ET.tostring(root, encoding='unicode'))
        powershell(f"Start-ScheduledTask -TaskName '{task.name}' -TaskPath '\\'")
        deadline = time.monotonic() + 115
        while time.monotonic() < deadline:
            info = json.loads(powershell(f"$t=Get-ScheduledTask -TaskName '{task.name}';$i=Get-ScheduledTaskInfo -TaskName '{task.name}';@{{state=[string]$t.State;exit=$i.LastTaskResult}}|ConvertTo-Json -Compress"))
            if report.exists() and info['state'] != 'Running':
                break
            time.sleep(1)
        assert report.exists() and info['state'] != 'Running', info
        result = {'task': info, 'report': json.loads(report.read_text('utf-8'))}
        assert result['report']['message']['claim_attempted'] is False
    finally:
        if task.get() is not None:
            task.remove()
        result.update(temporary_task_removed=task.get() is None,
                      production_task_unchanged=WindowsTask().get() == original)
        (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    print(str(output / 'result.json'))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
