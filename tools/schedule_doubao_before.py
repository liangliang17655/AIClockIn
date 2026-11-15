"""One-off next-day observation only, never a check-in task."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aiclockin.schedule import WindowsTask
from aiclockin.package import data_root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paired', action='store_true', help='Capture bound activity and official ledger together; never claim')
    parser.add_argument('--data', type=Path)
    args = parser.parse_args()
    now = datetime.now(timezone(timedelta(hours=8)))
    moment = (now + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    task = WindowsTask('AIClockIn-Doubao-Before-' + moment.strftime('%Y%m%d'))
    if task.get() is not None:
        raise SystemExit('Task already exists; refusing to overwrite')
    base = Path(__file__).resolve().parents[1]
    output = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork') / ('task028' if args.paired else 'task023') / moment.strftime('%Y%m%d')
    output.mkdir(parents=True, exist_ok=True)
    observation = output / 'before-candidate.json'
    if observation.exists() or (output/'registration.json').exists() or (output/'before-bundle').exists():
        raise SystemExit('Observation already exists; refusing to overwrite')
    python = Path(sys.executable).resolve()
    if python.with_name('pythonw.exe').exists():
        python = python.with_name('pythonw.exe')
    ns = 'http://schemas.microsoft.com/windows/2004/02/mit/task'
    ET.register_namespace('', ns)
    root = ET.Element('{' + ns + '}Task', version='1.2')
    def node(parent, name, value=None):
        child = ET.SubElement(parent, '{' + ns + '}' + name); child.text = value
        return child
    trigger = node(node(root, 'Triggers'), 'TimeTrigger')
    node(trigger, 'StartBoundary', moment.isoformat())
    node(trigger, 'Enabled', 'true')
    principal = node(node(root, 'Principals'), 'Principal'); principal.set('id', 'Owner')
    node(principal, 'UserId', task.user)
    node(principal, 'LogonType', 'InteractiveToken'); node(principal, 'RunLevel', 'LeastPrivilege')
    settings = node(root, 'Settings')
    node(settings, 'ExecutionTimeLimit', 'PT5M' if args.paired else 'PT1M'); node(settings, 'MultipleInstancesPolicy', 'IgnoreNew')
    node(settings, 'DisallowStartIfOnBatteries', 'false'); node(settings, 'StopIfGoingOnBatteries', 'false')
    node(settings, 'StartWhenAvailable', 'false')  # Do not take a late sample and call it "before".
    actions = node(root, 'Actions'); actions.set('Context', 'Owner')
    action = node(actions, 'Exec'); node(action, 'Command', str(python))
    arguments = ['-B', str(base / 'tools/doubao_compare.py'), 'capture', '--label',
                 'scheduled-before-candidate-unverified', '--screenshot', '--out', str(observation)]
    if args.paired:
        arguments = ['-B', str(base/'tools/sample_doubao_day.py'), '--day', moment.date().isoformat(),
                     '--data', str((args.data or data_root(base)).resolve()), '--out', str(output/'before-bundle')]
    node(action, 'Arguments', subprocess.list2cmdline(arguments))
    node(action, 'WorkingDirectory', str(base))
    task.put(ET.tostring(root, encoding='unicode'))
    assert task.get() is not None
    result = {'task': task.name, 'at': moment.isoformat(), 'out': str(output/'before-bundle' if args.paired else observation), 'exe': str(python),
              'claim_enabled': False, 'late_catchup': False,
              'paired_bundle': args.paired,
              'conditions': ('Confirmed source binding; original Windows user logged in/unlocked, awake, D available. Startup/navigation failure is preserved; no claim.' if args.paired else
                             'Current user logged in/unlocked; official activity tab loaded. A computer date is not business state proof.')}
    (output / 'registration.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
