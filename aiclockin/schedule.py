"""One independent Windows task. Never touches DailyCheckin's tasks."""
import base64
from datetime import date
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from .store import OperationLock, write_json

TASK = 'AIClockIn-Auto'
TIMES = ('08:45', '11:45', '14:45', '17:45', '20:45', '23:45')
NAMESPACE = 'http://schemas.microsoft.com/windows/2004/02/mit/task'
NS = {'t': NAMESPACE}


def powershell(script):
    script = "$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);" + script
    encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
        capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=45)
    if result.returncode:
        raise RuntimeError('Windows 自动任务操作失败，请检查当前用户权限后重试')
    return result.stdout.decode('utf-8-sig', 'replace').strip()


class WindowsTask:
    def __init__(self, name=TASK):
        self.name = name
        self.user = powershell('[Security.Principal.WindowsIdentity]::GetCurrent().User.Value')

    def get(self):
        return powershell(f"$t=Get-ScheduledTask -TaskPath '\\' | Where-Object {{$_.TaskName -eq '{self.name}'}};if($t){{Export-ScheduledTask -TaskName '{self.name}' -TaskPath '\\'}}") or None

    def put(self, xml):
        value = base64.b64encode(xml.encode('utf-8')).decode('ascii')
        powershell(f"$x=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{value}'));Register-ScheduledTask -TaskName '{self.name}' -TaskPath '\\' -Xml $x -Force | Out-Null")

    def remove(self):
        powershell(f"Unregister-ScheduledTask -TaskName '{self.name}' -TaskPath '\\' -Confirm:$false")


def arguments(data):
    return subprocess.list2cmdline(['--silent', '--data', str(Path(data).resolve())])


def definition(exe, user, data):
    ET.register_namespace('', NAMESPACE)
    root = ET.Element('{' + NAMESPACE + '}Task', version='1.2')
    def node(parent, tag, text=None):
        child = ET.SubElement(parent, '{' + NAMESPACE + '}' + tag)
        child.text = text
        return child
    node(node(root, 'RegistrationInfo'), 'Description', 'AIClockIn independent background check-in')
    triggers = node(root, 'Triggers')
    for moment in TIMES:
        trigger = node(triggers, 'CalendarTrigger')
        node(trigger, 'StartBoundary', date.today().isoformat() + 'T' + moment + ':00')
        node(node(trigger, 'ScheduleByDay'), 'DaysInterval', '1')
    login = node(triggers, 'LogonTrigger')
    node(login, 'Delay', 'PT30S')
    node(login, 'UserId', user)
    event = node(triggers, 'EventTrigger')
    node(event, 'Subscription', '<QueryList><Query Id="0" Path="System"><Select Path="System">*[System[(Provider[@Name=\'Microsoft-Windows-Kernel-Power\'] and EventID=107) or (Provider[@Name=\'Microsoft-Windows-Power-Troubleshooter\'] and EventID=1)]]</Select></Query></QueryList>')
    node(event, 'Delay', 'PT15S')
    principal = node(node(root, 'Principals'), 'Principal')
    principal.set('id', 'Owner')
    node(principal, 'UserId', user)
    node(principal, 'LogonType', 'InteractiveToken')
    node(principal, 'RunLevel', 'LeastPrivilege')
    settings = node(root, 'Settings')
    for key, value in [('MultipleInstancesPolicy', 'IgnoreNew'), ('DisallowStartIfOnBatteries', 'false'),
        ('StopIfGoingOnBatteries', 'false'), ('StartWhenAvailable', 'true'), ('Enabled', 'true'), ('ExecutionTimeLimit', 'PT1H')]:
        node(settings, key, value)
    actions = node(root, 'Actions')
    actions.set('Context', 'Owner')
    action = node(actions, 'Exec')
    node(action, 'Command', str(exe))
    node(action, 'Arguments', arguments(data))
    node(action, 'WorkingDirectory', str(exe.parent))
    return ET.tostring(root, encoding='unicode')


def matches(xml, exe, user, data):
    try:
        root = ET.fromstring(xml)
        actual = root.findtext('t:Actions/t:Exec/t:Command', namespaces=NS)
        triggers = root.find('t:Triggers', NS)
        return (actual is not None and Path(actual).resolve() == exe.resolve()
            and root.findtext('t:Actions/t:Exec/t:Arguments', namespaces=NS) == arguments(data)
            and root.findtext('t:Principals/t:Principal/t:UserId', namespaces=NS) == user
            and root.findtext('t:Principals/t:Principal/t:LogonType', namespaces=NS) == 'InteractiveToken'
            and root.findtext('t:Principals/t:Principal/t:RunLevel', default='LeastPrivilege', namespaces=NS) == 'LeastPrivilege'
            and root.findtext('t:Settings/t:Enabled', default='true', namespaces=NS) == 'true'
            and triggers is not None and len(triggers) == 8)
    except (ValueError, ET.ParseError, TypeError):
        return False


class TaskManager:
    def __init__(self, root, exe, backend=None):
        self.root, self.exe = Path(root), Path(exe)
        if not self.exe.is_absolute() or not self.exe.is_file() or self.exe.suffix.lower() != '.exe':
            raise ValueError('请从 AIClockIn.exe 设置后台自动签到')
        self.backend = backend or WindowsTask()

    def status(self):
        xml = self.backend.get()
        if xml is None:
            return {'enabled': False, 'label': '自动签到未开启', 'detail': '点击开启后，无需打开窗口，Windows 会自动执行。'}
        if matches(xml, self.exe, self.backend.user, self.root):
            return {'enabled': True, 'label': '自动签到已开启', 'detail': '每天 ' + ' / '.join(TIMES) + '；进入桌面、睡眠恢复后也会补跑。'}
        return {'enabled': False, 'label': '自动任务需要更新', 'detail': '点击开启，修复当前任务的路径或设置。'}

    def change(self, enabled):
        with OperationLock(self.root):
            before = self.backend.get()
            backup = self.root / 'task-backup.json'
            write_json(backup, {'name': getattr(self.backend, 'name', TASK), 'xml': before})
            try:
                if enabled:
                    self.backend.put(definition(self.exe, self.backend.user, self.root))
                    if not matches(self.backend.get(), self.exe, self.backend.user, self.root):
                        raise RuntimeError('自动任务注册后核验失败')
                elif before is not None:
                    self.backend.remove()
                    if self.backend.get() is not None:
                        raise RuntimeError('自动任务未能移除')
            except Exception as exc:
                try:
                    if before is not None:
                        self.backend.put(before)
                        if ET.tostring(ET.fromstring(self.backend.get())) != ET.tostring(ET.fromstring(before)):
                            raise RuntimeError()
                    elif self.backend.get() is not None:
                        self.backend.remove()
                except Exception:
                    raise RuntimeError(f'操作未完成，恢复也未能确认；原任务备份在 {backup}') from exc
                raise RuntimeError('操作未完成，已恢复原任务') from exc

    def enable(self):
        self.change(True)

    def disable(self):
        self.change(False)
