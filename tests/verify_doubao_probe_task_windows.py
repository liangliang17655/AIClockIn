"""Opt-in real InteractiveToken task runs of the non-claiming UIA spike."""
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
    base = Path(__file__).resolve().parents[1]
    output = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/task022')
    output.mkdir(parents=True, exist_ok=True)
    probe = output / 'task-probe.json'
    task = WindowsTask('AIClockIn-DoubaoProbe-' + uuid.uuid4().hex[:12])
    original = WindowsTask().get()
    ns = 'http://schemas.microsoft.com/windows/2004/02/mit/task'
    ET.register_namespace('', ns)
    root = ET.Element('{' + ns + '}Task', version='1.2')
    def node(parent, name, value=None):
        child = ET.SubElement(parent, '{' + ns + '}' + name)
        child.text = value
        return child
    principal = node(node(root, 'Principals'), 'Principal')
    principal.set('id', 'Owner')
    node(principal, 'UserId', task.user)
    node(principal, 'LogonType', 'InteractiveToken')
    node(principal, 'RunLevel', 'LeastPrivilege')
    settings = node(root, 'Settings')
    node(settings, 'ExecutionTimeLimit', 'PT1M')
    node(settings, 'MultipleInstancesPolicy', 'IgnoreNew')
    node(settings, 'DisallowStartIfOnBatteries', 'false')
    node(settings, 'StopIfGoingOnBatteries', 'false')
    actions = node(root, 'Actions'); actions.set('Context', 'Owner')
    action = node(actions, 'Exec')
    node(action, 'Command', str(Path(sys.executable).resolve()))
    node(action, 'Arguments', subprocess.list2cmdline(['-B', str(base / 'tools/probe_doubao_signin.py'),
         '--samples', '1', '--restore', '--navigate', '--reveal', '--out', str(probe)]))
    node(action, 'WorkingDirectory', str(base))
    results = []
    try:
        task.put(ET.tostring(root, encoding='unicode'))
        for index in range(3):
            probe.unlink(missing_ok=True)
            powershell(f"Start-ScheduledTask -TaskName '{task.name}' -TaskPath '\\'")
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                info = json.loads(powershell(f"$t=Get-ScheduledTask -TaskName '{task.name}';$i=Get-ScheduledTaskInfo -TaskName '{task.name}';@{{state=[string]$t.State;exit=$i.LastTaskResult}}|ConvertTo-Json -Compress"))
                if probe.exists() and info['state'] != 'Running':
                    break
                time.sleep(.5)
            assert probe.exists() and info['exit'] == 0 and info['state'] != 'Running', info
            data = json.loads(probe.read_text('utf-8'))
            assert data['claim_clicked'] is False
            results.append({'run': index + 1, 'task': info, 'observation': data})
    finally:
        if task.get() is not None:
            task.remove()
        summary = {'runs': results, 'temporary_task_removed': task.get() is None,
                   'production_task_unchanged': WindowsTask().get() == original,
                   'claim_clicked': False, 'sign_state_verified': False}
        (output / 'scheduled-results.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'runs': len(results), 'contexts': [len(r['observation']['samples'][0].get('signin_contexts', [])) for r in results],
                      'temporary_task_removed': summary['temporary_task_removed'],
                      'production_task_unchanged': summary['production_task_unchanged'], 'claim_clicked': False}))


if __name__ == '__main__':
    main()
