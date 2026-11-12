from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aiclockin import setup_update as u
from aiclockin import package
from aiclockin.update import ROOT,file_hash
from aiclockin.store import Store


class SetupUpdateTests(unittest.TestCase):
    def setUp(self):
        ROOT.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=ROOT);self.root=Path(self.temp.name)
        self.target=self.root/'app/AIClockIn.exe';self.target.parent.mkdir();self.target.write_bytes(b'old')
        runtime=self.target.parent/'_runtime-v0.4.0';runtime.mkdir();(runtime/'python.dll').write_bytes(b'old-runtime')
        package.write_manifest(self.target.parent,'0.4.0')
        self.data=self.target.parent/'data';Store(self.data).save_accounts([])
        self.before=(self.data/'accounts.json').read_bytes()
        self.candidate=self.root/'Setup.exe';self.candidate.write_bytes(b'setup')
        with patch.object(u,'capture_registry',return_value=None):
            self.manifest=u.prepare(self.target,self.candidate,self.data,'0.4.1',file_hash(self.candidate))
    def tearDown(self):self.temp.cleanup()

    def test_helper_has_full_runtime_and_no_data(self):
        helper=self.manifest.parent/'helper'
        self.assertTrue((helper/'_runtime-v0.4.0/python.dll').exists())
        self.assertFalse((helper/'data').exists())

    def test_installer_failure_restores_old_program(self):
        def install(*args):self.target.write_bytes(b'broken');return 1
        with patch.object(u,'run_setup',side_effect=install),patch.object(u,'restore_registry'):
            with self.assertRaises(u.SetupError):u.execute(self.manifest)
        self.assertEqual(self.target.read_bytes(),b'old')
        self.assertEqual((self.data/'accounts.json').read_bytes(),self.before)

    def test_health_failure_restores_even_after_setup_success(self):
        def install(*args):self.target.write_bytes(b'new');return 0
        with patch.object(u,'run_setup',side_effect=install),patch.object(u,'health_check',side_effect=RuntimeError('bad')),patch.object(u,'restore_registry'):
            with self.assertRaises(u.SetupError):u.execute(self.manifest)
        self.assertEqual(self.target.read_bytes(),b'old')

    def test_success_and_custom_data_arguments(self):
        with patch.object(u,'run_setup',return_value=0) as run,patch.object(u,'health_check',return_value=True):u.execute(self.manifest)
        self.assertEqual(u.load(self.manifest)['state'],'committed')
        self.assertIn('/DATA='+str(self.data),u.setup_command(u.load(self.manifest),self.manifest))


if __name__=='__main__':unittest.main()
