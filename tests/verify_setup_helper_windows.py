"""Actual folder helper -> native Setup -> health -> GUI restart, in isolated files."""
import json
from pathlib import Path
import tempfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from aiclockin.runtime import prepare
from aiclockin.store import Store,write_json
from aiclockin.update import file_hash
from aiclockin import setup_update
from aiclockin.update_apply import start
from tests.verify_inno_windows import OUTPUT,run,snapshot,health
from tests.verify_install_windows import wait_until,close_app,titles


def main():
    prepare()
    prior=json.loads((OUTPUT/'inno-windows.json').read_text('utf-8'))
    group=prior['app_id']
    a=OUTPUT/'AIClockIn-v0.4.0-Setup-windows-x64.exe'
    b=OUTPUT/'AIClockIn-v0.4.1-Setup-windows-x64.exe'
    bad=OUTPUT/'AIClockIn-Test-Failure.exe'
    with tempfile.TemporaryDirectory(prefix='setup-helper-') as folder:
        folder=Path(folder);installed=folder/'app';exe=installed/'AIClockIn.exe';data=installed/'data'
        options=['/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/DIR='+str(installed),'/DATA='+str(data),'/GROUP='+group,'/TASKS=']
        assert run([a,*options,'/LOG='+str(folder/'install.log')],folder/'install-process.log')==0
        uninstall=next(installed.glob('unins*.exe'))
        try:
            store=Store(data);store.save_accounts([])
            store.record('synthetic','workbuddy','offline','失败',None,None,'helper history')
            write_json(data/'update-settings.json',{'auto_check':False})
            before=snapshot(data)
            manifest=setup_update.prepare(exe,b,data,'0.4.1',file_hash(b))
            helper_dir=manifest.parent/'helper'
            assert not (helper_dir/'data').exists()
            assert any(helper_dir.glob('_runtime-v*'))
            gui=start([str(exe),'--data',str(data)],installed)
            wait_until(lambda:'AIClockIn · 每日签到' in titles(exe))
            helper=setup_update.launch_helper(manifest,gui.pid)
            close_app(exe);gui.wait(timeout=15)
            assert helper.wait(timeout=180)==0
            outcome=json.loads((manifest.parent/'result.json').read_text('utf-8'))
            assert outcome['ok'] and outcome['state']=='committed',outcome
            wait_until(lambda:'AIClockIn · 每日签到' in titles(exe))
            close_app(exe)
            health(exe,folder,'0.4.1');assert before==snapshot(data)
            rollback=setup_update.prepare(exe,bad,data,'0.4.1',file_hash(bad))
            try:
                setup_update.execute(rollback)
                raise AssertionError('Expected native installer failure')
            except setup_update.SetupError:
                assert setup_update.load(rollback)['state']=='restored'
            health(exe,folder,'0.4.1');assert before==snapshot(data)
            report={'full_runtime_helper':True,'native_setup_called':True,'version':'0.4.1',
                    'automatic_gui_restart':True,'data_history_preserved':True,'native_failure_restored':True,
                    'transaction':str(manifest)}
            write_json(OUTPUT/'setup-helper.json',report)
            print(json.dumps(report,ensure_ascii=False))
        finally:
            close_app(exe)
            if uninstall.exists():assert run([uninstall,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],OUTPUT/'helper-uninstall.log')==0


if __name__=='__main__':main()
