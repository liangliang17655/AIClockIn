"""Real native health validation; all accounts, tasks and installer IDs are isolated."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid
import winreg
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aiclockin.runtime import prepare
from aiclockin.package import copy_bundle
from aiclockin.store import Store,write_json
from aiclockin.update import file_hash
from aiclockin.schedule import TaskManager,WindowsTask
from tests.verify_inno_windows import ISCC,BASE,run,snapshot

OUTPUT=Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/install-diagnostics')
VERSION=(BASE/'VERSION').read_text('utf-8').strip()
BUNDLE=BASE/f'dist/bundle/v{VERSION}/AIClockIn'
BASELINE=BASE/'dist/bundle/v0.4.2/AIClockIn'


def compile_setup(bundle,app_id,name,version=None,timeout=90000):
    version=version or VERSION
    runtime=json.loads((bundle/'bundle-manifest.json').read_text('utf-8'))['runtime']
    code=run([ISCC,'/DAppVersion='+version,'/DRuntimeDir='+runtime,'/DBundleDir='+str(bundle),
              '/DReleaseDir='+str(OUTPUT),'/DAppId='+app_id,'/DShortcutName='+app_id,
              '/DHealthTimeoutMs='+str(timeout),'/F'+name,BASE/'installer/AIClockIn.iss'],OUTPUT/(name+'-compile.log'))
    assert code==0,name
    return OUTPUT/(name+'.exe')


def main():
    prepare();OUTPUT.mkdir(parents=True,exist_ok=True)
    app_id='AIClockIn-Diagnostics-'+uuid.uuid4().hex[:12]
    result={};task=WindowsTask(app_id)
    with tempfile.TemporaryDirectory(prefix='install-diagnostics-') as folder:
        folder=Path(folder);target=folder/'中文 app';data=folder/'private data';exe=target/'AIClockIn.exe'
        baseline=folder/'baseline';copy_bundle(BASELINE,baseline)
        baseline_version=json.loads((baseline/'bundle-manifest.json').read_text('utf-8'))['version']
        prior=compile_setup(baseline,app_id,'baseline',version=baseline_version)
        good=compile_setup(BUNDLE,app_id,'healthy')
        timeout=compile_setup(BUNDLE,app_id,'timeout',timeout=1)
        mismatch=compile_setup(BUNDLE,app_id,'version-mismatch',version='9.9.9')
        options=['/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOCLOSEAPPLICATIONS',
                 '/DIR='+str(target),'/DATA='+str(data),'/GROUP='+app_id,'/TASKS=']
        uninstall=None
        try:
            assert run([prior,*options],OUTPUT/'baseline.log')==0
            uninstall=next(target.glob('unins*.exe'))
            store=Store(data);rows=[{'id':'fixture','platform':'workbuddy','name':'offline',
                                    'enabled':False,'credentials':{'uid':'synthetic','access_token':'synthetic'}}]
            store.save_accounts(rows);store.record('fixture','workbuddy','offline','失败',None,None,'synthetic fixture')
            TaskManager(data,exe,task).enable();xml=ET.tostring(ET.fromstring(task.get()))
            before=snapshot(data);old=file_hash(exe)
            assert run([timeout,*options],OUTPUT/'timeout.log')==10
            assert file_hash(exe)==old, 'rollback executable differs from baseline'
            assert before==snapshot(data), 'data changed: '+str([k for k in set(before)|set(snapshot(data)) if before.get(k)!=snapshot(data).get(k)])
            logs=[p.read_text('utf-8-sig') for p in target.glob('diagnostics/*/install.log')]
            assert any('超时' in s and '1 ms' in s for s in logs)
            result['real_timeout_exit10_rollback_data_preserved']=True
            assert run([mismatch,*options],OUTPUT/'version-mismatch.log')==10
            logs=[p.read_text('utf-8-sig') for p in target.glob('diagnostics/*/install.log')]
            assert any('期望 9.9.9' in s for s in logs)
            assert file_hash(exe)==old, 'rollback executable differs from baseline'
            assert before==snapshot(data), 'data changed: '+str([k for k in set(before)|set(snapshot(data)) if before.get(k)!=snapshot(data).get(k)])
            assert ET.tostring(ET.fromstring(task.get()))==xml
            assert Store(data).accounts()==rows
            result['version_mismatch_rollback_and_task_unchanged']=True
            assert run([good,*options],OUTPUT/'healthy.log')==0
            assert before==snapshot(data)
            report=next(p for p in target.glob('diagnostics/*/health.json') if json.loads(p.read_text('utf-8')).get('ok') and json.loads(p.read_text('utf-8')).get('version')==VERSION)
            health=json.loads(report.read_text('utf-8'))
            assert health['ok'] and health['version']==VERSION
            assert Path(health['work']).is_relative_to(report.parent)
            assert '个人开发软件' not in str(report.relative_to(target))
            result['native_success_report_on_d']=True
            # Break a dependency in a FIRST install (no old dependency can mask it).
            broken=folder/'broken-bundle';copy_bundle(BUNDLE,broken)
            dependency=next(broken.rglob('_tkinter.pyd'));dependency.unlink()
            broken_id=app_id+'-missing';bad=compile_setup(broken,broken_id,'missing-dependency')
            broken_target=folder/'broken-install'
            assert run([bad,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/DIR='+str(broken_target),
                        '/DATA='+str(folder/'unused-data'),'/GROUP='+broken_id,'/TASKS='],OUTPUT/'missing-dependency.log')==10
            failure=json.loads(next(broken_target.glob('diagnostics/*/health.json')).read_text('utf-8'))
            assert not failure['ok'] and failure['stage']=='imports'
            assert '_tkinter' in failure['traceback'] and failure['error_type'] in ('ImportError','ModuleNotFoundError')
            assert not (broken_target/'AIClockIn.exe').exists()
            result['missing_dependency_type_stage_traceback_preserved']=True
            for n,p in enumerate(target.glob('diagnostics/*/install.log')):shutil.copy2(p,OUTPUT/('diagnostic-'+str(n)+'.log'))
            shutil.copy2(next(broken_target.glob('diagnostics/*/health.json')),OUTPUT/'missing-dependency-health.json')
        finally:
            for n,p in enumerate(target.glob('diagnostics/*/install.log')):shutil.copy2(p,OUTPUT/('diagnostic-'+str(n)+'.log'))
            if task.get() is not None:task.remove()
            if uninstall and uninstall.exists():assert run([uninstall,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],OUTPUT/'uninstall.log')==0
            for key in (app_id,app_id+'-missing'):
                try:winreg.DeleteKey(winreg.HKEY_CURRENT_USER,'Software'+chr(92)+key)
                except FileNotFoundError:pass
    write_json(OUTPUT/'results.json',result)
    print(json.dumps(result,ensure_ascii=False))

def verify_shortcuts():
    from aiclockin.installer import shell
    from tests.verify_install_windows import read_link,wait_until,titles,close_app
    from aiclockin.update_apply import start
    prepare();OUTPUT.mkdir(parents=True,exist_ok=True)
    app_id='AIClockIn-ShortcutCheck-'+uuid.uuid4().hex[:10]
    setup=compile_setup(BUNDLE,app_id,'shortcut-check')
    paths=shell("$s=New-Object -ComObject WScript.Shell;@{desktop=$s.SpecialFolders.Item('Desktop');programs=$s.SpecialFolders.Item('Programs')}|ConvertTo-Json -Compress",{})
    desktop=Path(paths['desktop'])/(app_id+'.lnk');menu=Path(paths['programs'])/app_id/'AIClockIn.lnk'
    with tempfile.TemporaryDirectory(prefix='native-shortcut-') as folder:
        folder=Path(folder);target=folder/'中文安装目录';data=folder/'private data'
        uninstall=None
        try:
            assert run([setup,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/DIR='+str(target),
                        '/DATA='+str(data),'/GROUP='+app_id,'/TASKS=desktopicon'],OUTPUT/'shortcut-check.log')==0
            uninstall=next(target.glob('unins*.exe'))
            for link in (desktop,menu):
                assert link.exists(),str(link)
                value=read_link(link)
                assert Path(value['target'])==target/'AIClockIn.exe'
                assert value['arguments']==subprocess.list2cmdline(['--data',str(data)])
            Store(data).save_accounts([])
            write_json(data/'update-settings.json',{'auto_check':False})
            gui=start([str(target/'AIClockIn.exe'),'--data',str(data)],target)
            try:
                wait_until(lambda:'AIClockIn · 每日签到' in titles(target/'AIClockIn.exe'))
                assert (target/'.runtime').is_dir()
                assert gui.poll() is None
            finally:
                close_app(target/'AIClockIn.exe');gui.wait(timeout=15)
            print('PASS: fresh native install creates correct shortcuts; normal GUI launches with local runtime cache.')
        finally:
            if uninstall and uninstall.exists():assert run([uninstall,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],OUTPUT/'shortcut-uninstall.log')==0
            try:winreg.DeleteKey(winreg.HKEY_CURRENT_USER,'Software'+chr(92)+app_id)
            except FileNotFoundError:pass
    assert not desktop.exists() and not menu.exists()
    write_json(OUTPUT/'shortcuts.json',{'fresh_desktop_and_start_menu':True,'correct_target_and_data':True,'normal_gui_local_runtime':True,'uninstall_cleans_own_links':True})


if __name__=='__main__':
    OUTPUT=OUTPUT/('v'+VERSION)
    if '--shortcuts-only' in sys.argv:verify_shortcuts()
    else:main()
