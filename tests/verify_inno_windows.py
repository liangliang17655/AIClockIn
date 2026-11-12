"""Explicit native Inno integration in D-drive fixtures, unique links/registry/task."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid
import winreg
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from aiclockin.runtime import prepare
from aiclockin.store import Store,write_json
from aiclockin.update import file_hash
from aiclockin.update_apply import child_env,start
from aiclockin.schedule import TaskManager,WindowsTask,powershell
from aiclockin.installer import shell
from tests.verify_install_windows import wait_until,close_app,titles,read_link

BASE=Path(__file__).resolve().parent.parent
ISCC=Path('D:/个人开发软件/AI工作区/temp/AIClockIn-tools/InnoSetup-7.1.1/ISCC.exe')
PYTHON=Path('D:/个人开发软件/AI工作区/temp/DailyCheckin-build/venv/Scripts/python.exe')
OUTPUT=Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/inno')


def run(command,log,timeout=180):
    with Path(log).open('wb') as stream:
        result=subprocess.run(list(map(str,command)),cwd=BASE,env=child_env(),stdout=stream,stderr=subprocess.STDOUT,
                              timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
    return result.returncode


def compile_setup(bundle,version,app_id,name,fail=False):
    runtime=json.loads((bundle/'bundle-manifest.json').read_text('utf-8')).get('runtime','_runtime-v'+version)
    args=[ISCC,f'/DAppVersion={version}',f'/DRuntimeDir={runtime}',f'/DBundleDir={bundle}',f'/DReleaseDir={OUTPUT}',f'/DAppId={app_id}',f'/DShortcutName={name}']
    if fail:args+=['/DForceHealthFailure=1','/FAIClockIn-Test-Failure']
    code=run([*args,BASE/'installer/AIClockIn.iss'],OUTPUT/('failure-compile.log' if fail else 'compile-'+version+'.log'))
    assert code==0,'Inspect compiler log'
    return OUTPUT/('AIClockIn-Test-Failure.exe' if fail else f'AIClockIn-v{version}-Setup-windows-x64.exe')


def snapshot(data):return {p.name:file_hash(p) for p in data.iterdir() if p.is_file() and p.name!='operation.lock'}


def health(exe,folder,version):
    report=folder/('health-'+version+'.json')
    assert run([exe,'--self-test','--report',report],folder/('health-'+version+'.log'))==0
    assert json.loads(report.read_text('utf-8'))['version']==version


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--reuse-bundle',action='store_true');args=parser.parse_args()
    prepare();OUTPUT.mkdir(parents=True,exist_ok=True)
    token=uuid.uuid4().hex[:12];app_id='AIClockIn-Test-'+token;link_name=app_id
    key_name=r'Software\Microsoft\Windows\CurrentVersion\Uninstall'+chr(92)+app_id+'_is1'
    task=WindowsTask('AIClockIn-InnoTest-'+token)
    fixture=OUTPUT/'version-0.4.1';fixture.mkdir(exist_ok=True);(fixture/'VERSION').write_text('0.4.1\n',encoding='utf-8')
    bundle_a=BASE/'dist/bundle/v0.4.0/AIClockIn';destination=BASE/'dist/test-bundle/v0.4.1'
    if not args.reuse_bundle:
        assert run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',BASE/'build.ps1',
                    '-BuildPython',PYTHON,'-Destination',destination,'-VersionFile',fixture/'VERSION'],OUTPUT/'test-bundle-build.log')==0
    bundle_b=destination/'AIClockIn'
    a=compile_setup(bundle_a,'0.4.0',app_id,link_name)
    b=compile_setup(bundle_b,'0.4.1',app_id,link_name)
    failed=compile_setup(bundle_b,'0.4.1',app_id,link_name,True)
    result={'app_id':app_id,'task':task.name,'project_version_unchanged':(BASE/'VERSION').read_text().strip()=='0.4.0'}
    with tempfile.TemporaryDirectory(prefix='inno-install-') as folder:
        folder=Path(folder);installed=folder/'installed';data=installed/'custom-data';exe=installed/'AIClockIn.exe'
        options=['/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOCLOSEAPPLICATIONS','/DIR='+str(installed),'/DATA='+str(data),'/GROUP='+link_name,'/TASKS=desktopicon']
        uninstall=None
        try:
            assert run([a,*options,'/LOG='+str(folder/'install.log')],folder/'install-process.log')==0
            uninstall=next(installed.glob('unins*.exe'));health(exe,folder,'0.4.0')
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key_name,0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:
                assert winreg.QueryValueEx(key,'DisplayVersion')[0]=='0.4.0'
            paths=shell("$s=New-Object -ComObject WScript.Shell;@{desktop=$s.SpecialFolders.Item('Desktop');programs=$s.SpecialFolders.Item('Programs')}|ConvertTo-Json -Compress",{})
            desktop=Path(paths['desktop'])/(link_name+'.lnk');menu=Path(paths['programs'])/link_name/'AIClockIn.lnk'
            assert desktop.exists() and menu.exists()
            assert Path(read_link(desktop)['target'])==exe and str(data) in read_link(menu)['arguments']
            assert read_link(desktop)['arguments']==subprocess.list2cmdline(['--data',str(data)])
            store=Store(data);rows=[{'id':'synthetic','platform':'workbuddy','name':'offline','enabled':False,'credentials':{'uid':'synthetic','access_token':'synthetic'}}]
            store.save_accounts(rows);store.record('synthetic','workbuddy','offline','失败',None,None,'offline Inno test')
            write_json(data/'update-settings.json',{'auto_check':False})
            manager=TaskManager(data,exe,task);manager.enable()
            original_xml=ET.tostring(ET.fromstring(task.get()));before=snapshot(data);old_hash=file_hash(exe)
            gui=start([str(exe),'--data',str(data)],installed)
            wait_until(lambda:'AIClockIn · 每日签到' in titles(exe))
            assert run([b,*options,'/LOG='+str(folder/'occupied.log')],folder/'occupied-process.log')!=0
            assert gui.poll() is None and file_hash(exe)==old_hash
            close_app(exe);gui.wait(timeout=15);result['running_app_refused_without_kill']=True
            assert run([failed,*options,'/LOG='+str(folder/'failure.log')],folder/'failure-process.log')!=0
            assert file_hash(exe)==old_hash,'Native rollback lost original launcher'
            health(exe,folder,'0.4.0');assert before==snapshot(data);result['native_failure_restored_old_version']=True
            assert run([b,*options,'/LOG='+str(folder/'upgrade.log')],folder/'upgrade-process.log')==0
            health(exe,folder,'0.4.1');assert before==snapshot(data) and Store(data).accounts()==rows
            assert original_xml==ET.tostring(ET.fromstring(task.get()))
            powershell(f"Start-ScheduledTask -TaskName '{task.name}'")
            def ran():
                value=json.loads(powershell(f"$t=Get-ScheduledTask -TaskName '{task.name}';$i=Get-ScheduledTaskInfo -TaskName '{task.name}';@{{state=[string]$t.State;code=$i.LastTaskResult;ran=($i.LastRunTime.Year -gt 2020)}}|ConvertTo-Json -Compress"))
                return value if value['ran'] and value['state']!='Running' else None
            assert wait_until(ran)['code']==1
            result.update({'native_install':True,'desktop_start_menu':True,'hkcu_uninstall_registration':True,'upgrade_data_dpapi_preserved':True,'task_xml_and_execution_preserved':True})
            assert run([b,*options,'/LOG='+str(folder/'repeat.log')],folder/'repeat-process.log')==0
            assert before==snapshot(data)
            assert run([uninstall,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/LOG='+str(folder/'uninstall.log')],folder/'uninstall-process.log')==0
            wait_until(lambda:not exe.exists());assert before==snapshot(data)
            assert not desktop.exists() and not menu.exists()
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key_name):pass
                raise AssertionError('Uninstall key remains')
            except FileNotFoundError:pass
            result.update({'repeat_install_preserved':True,'uninstall_keeps_data_history':True,'uninstall_removes_links_registration':True})
        finally:
            close_app(exe)
            if task.get() is not None:task.remove()
            if uninstall and uninstall.exists():run([uninstall,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],OUTPUT/'cleanup-uninstall.log')
            result['temporary_task_cleaned']=task.get() is None;write_json(OUTPUT/'inno-windows.json',result)
            for p in folder.glob('*.log'):shutil.copyfile(p,OUTPUT/p.name)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
