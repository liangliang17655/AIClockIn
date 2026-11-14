"""Opt-in real full-runtime update helper using isolated native installer fixtures."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid
import winreg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aiclockin import setup_update
from aiclockin.runtime import prepare
from aiclockin.schedule import powershell
from aiclockin.store import Store, write_json
from aiclockin.update import file_hash
from tests.verify_inno_windows import run, snapshot


def ui_window(exe, close=False):
    # UIA only, scoped to a unique test executable path. Never target production.
    path = str(exe).replace("'", "''")
    action = "($w.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern)).Close();" if close else ''
    script = ("Add-Type -AssemblyName UIAutomationClient;Add-Type -AssemblyName UIAutomationTypes;"
              f"$ids=@(Get-CimInstance Win32_Process|Where-Object {{$_.ExecutablePath -eq '{path}'}}|ForEach-Object {{$_.ProcessId}});"
              "$ws=[System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition);"
              "$found=$false;foreach($w in $ws){if($ids -contains $w.Current.ProcessId -and $w.Current.Name -eq 'AIClockIn · 每日签到'){"
              + action + "$found=$true}};if($found){'found'}")
    return powershell(script).strip() == 'found'


def main():
    prepare()
    base = Path(__file__).resolve().parents[1]
    version = (base / 'VERSION').read_text('utf-8').strip()
    fixtures = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/install-diagnostics') / ('v' + version)
    output = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork')
    with tempfile.TemporaryDirectory(prefix='release-helper-') as directory:
        folder = Path(directory); target = folder / 'app'; data = folder / 'private data'
        exe = target / 'AIClockIn.exe'
        group = 'AIClockIn-HelperCheck-' + uuid.uuid4().hex[:12]
        options = ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOCLOSEAPPLICATIONS',
                   '/DIR=' + str(target), '/DATA=' + str(data), '/GROUP=' + group, '/TASKS=']
        assert run([fixtures / 'baseline.exe', *options], output / 'task017-helper-baseline.log') == 0
        uninstall = next(target.glob('unins*.exe'))
        key_name = None
        root_name = r'Software\Microsoft\Windows\CurrentVersion\Uninstall'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, root_name, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as root:
            for index in range(winreg.QueryInfoKey(root)[0]):
                name = winreg.EnumKey(root, index)
                if not name.startswith('AIClockIn-Diagnostics-'):
                    continue
                with winreg.OpenKey(root, name) as key:
                    if Path(winreg.QueryValueEx(key, 'InstallLocation')[0]).resolve() == target.resolve():
                        key_name = root_name + '\\' + name
        assert key_name, 'Isolated registration not found'
        original_key = setup_update.REGISTRY_KEY
        setup_update.REGISTRY_KEY = key_name
        try:
            store = Store(data)
            rows = [
                {'id': 'fixture-wb', 'platform': 'workbuddy', 'name': 'disabled WorkBuddy', 'enabled': False,
                 'credentials': {'uid': 'synthetic-wb', 'access_token': 'synthetic-wb'}},
                {'id': 'fixture-trae', 'platform': 'trae', 'name': 'disabled Trae', 'enabled': False,
                 'credentials': {'userId': 'synthetic-trae', 'accessToken': 'synthetic-trae'}},
            ]
            store.save_accounts(rows)
            for account in rows:
                store.record(account['id'], account['platform'], account['name'], '失败', None, None, 'No real credentials')
            write_json(data / 'update-settings.json', {'auto_check': False})
            before = snapshot(data)
            candidate = fixtures / 'healthy.exe'
            manifest = setup_update.prepare(exe, candidate, data, version, file_hash(candidate))
            # Exercise wait-for-old-PID with a disposable process, without closing user apps.
            sleeper = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(8)'], creationflags=subprocess.CREATE_NO_WINDOW)
            helper = setup_update.launch_helper(manifest, sleeper.pid)
            sleeper.wait(timeout=15)
            assert helper.wait(timeout=180) == 0
            result = json.loads((manifest.parent / 'result.json').read_text('utf-8'))
            assert result['ok'] and result['state'] == 'committed', result
            assert file_hash(exe) == file_hash(base / f'dist/bundle/v{version}/AIClockIn/AIClockIn.exe')
            assert snapshot(data) == before
            assert Store(data).accounts() == rows
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline and not ui_window(exe):
                time.sleep(.3)
            assert ui_window(exe), 'Automatic GUI restart not found'
            assert ui_window(exe, close=True)
            time.sleep(1)
            bad = fixtures / 'version-mismatch.exe'
            rollback = setup_update.prepare(exe, bad, data, version, file_hash(bad))
            try:
                setup_update.execute(rollback)
                raise AssertionError('Expected native version-check failure')
            except setup_update.SetupError:
                assert setup_update.load(rollback)['state'] == 'restored'
            assert snapshot(data) == before
            assert Store(data).accounts() == rows
            assert file_hash(exe) == file_hash(base / f'dist/bundle/v{version}/AIClockIn/AIClockIn.exe')
            result = {'version': version, 'real_full_runtime_helper': True, 'native_setup': True,
                      'automatic_gui_restart': True, 'data_hashes_preserved': True,
                      'native_failure_restored': True, 'both_platform_accounts_preserved': True,
                      'network_download_tested': False}
            write_json(output / f'task017-helper-{version}.json', result)
            print(json.dumps(result))
        finally:
            ui_window(exe, close=True)
            setup_update.REGISTRY_KEY = original_key
            if uninstall.exists():
                assert run([uninstall, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'], output / 'task017-helper-uninstall.log') == 0
            app_id = key_name.rsplit('\\', 1)[1].removesuffix('_is1')
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, 'Software\\' + app_id)
            except FileNotFoundError:
                pass


if __name__ == '__main__':
    main()
