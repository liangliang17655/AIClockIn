import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aiclockin.runtime import TEMP


class SelfCheckTests(unittest.TestCase):
    def setUp(self):
        TEMP.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=TEMP)
        self.report=Path(self.temp.name)/'diagnostics/health.json'
    def tearDown(self):self.temp.cleanup()

    def test_exception_has_stage_type_and_traceback(self):
        from aiclockin import selfcheck
        def fail(stage):
            stage('sqlite')
            raise RuntimeError('synthetic dependency failure')
        with patch.object(selfcheck,'perform',side_effect=fail):
            self.assertEqual(selfcheck.run(self.report),1)
        value=json.loads(self.report.read_text('utf-8'))
        self.assertFalse(value['ok']);self.assertEqual(value['stage'],'sqlite')
        self.assertEqual(value['error_type'],'RuntimeError')
        self.assertIn('synthetic dependency failure',value['traceback'])

    def test_prepare_failure_is_reported(self):
        from aiclockin import selfcheck
        with patch('aiclockin.runtime.prepare',side_effect=PermissionError('synthetic work permission')):
            self.assertEqual(selfcheck.run(self.report),1)
        value=json.loads(self.report.read_text('utf-8'))
        self.assertEqual(value['stage'],'prepare');self.assertEqual(value['error_type'],'PermissionError')

    def test_offline_with_no_task_probe_and_independent_work_directory(self):
        from aiclockin import selfcheck
        with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')), \
             patch('socket.create_connection',side_effect=AssertionError('network forbidden')), \
             patch('aiclockin.schedule.TaskManager.status',side_effect=AssertionError('task probe forbidden')), \
             patch.dict('os.environ',{'TEMP':'C:/Windows/Temp','TMP':'C:/Windows/Temp'}):
            self.assertEqual(selfcheck.run(self.report),0)
        value=json.loads(self.report.read_text('utf-8'))
        self.assertTrue(value['ok']);self.assertTrue(value['gui'])
        self.assertTrue(Path(value['work']).is_relative_to(self.report.parent))
        self.assertNotIn('synthetic-secret',self.report.read_text('utf-8'))

    def test_c_report_is_rejected_without_c_write(self):
        from aiclockin import selfcheck
        with self.assertRaisesRegex(ValueError,'D'):
            selfcheck.run(Path('C:/not-written/selfcheck.json'))

    def test_installer_health_report_never_uses_system_temp(self):
        script=(Path(__file__).resolve().parents[1]/'installer/AIClockIn.iss').read_text('utf-8-sig')
        self.assertNotIn("ExpandConstant('{tmp}\\health.json')",script)
        self.assertIn('HealthTimeoutMs',script)
        self.assertIn('GetExceptionMessage',script)

    def test_frozen_default_temp_belongs_to_install_not_developer(self):
        from aiclockin import runtime
        with patch('sys.frozen',True,create=True), patch('sys.executable',str(self.report.parent/'app/AIClockIn.exe')):
            self.assertEqual(runtime.default_temp(),self.report.parent/'app/.runtime')
