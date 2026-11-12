from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aiclockin import package
from aiclockin.runtime import TEMP
from aiclockin import update


class SetupPackageTests(unittest.TestCase):
    def setUp(self):
        TEMP.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=TEMP);self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()

    def test_install_info_preserves_custom_data(self):
        data=self.root/'custom data'
        (self.root/'install-info.ini').write_text('[Data]\nDirectory='+str(data)+'\n',encoding='utf-16')
        self.assertEqual(package.data_root(self.root),data)
        (self.root/'install-info.ini').unlink()
        self.assertEqual(package.data_root(self.root),self.root/'data')

    def test_runtime_marker_matches_inno_utf16_hash(self):
        self.assertEqual(package.unicode_md5('Test'),'8e06915d5f5d4f8754f51892d884c477')
        self.assertEqual(package.running_name(self.root/'AIClockIn.exe'),package.running_name(self.root/'aiclockin.exe'))

    def test_setup_is_preferred_over_legacy_exe(self):
        prefix='https://github.com/'+update.REPO+'/releases/download/v0.4.0/'
        names=['AIClockIn-v0.4.0-windows-x64.exe','AIClockIn-v0.4.0-Setup-windows-x64.exe']
        data={'tag_name':'v0.4.0','draft':False,'prerelease':False,'body':'setup',
              'assets':[{'name':name,'size':10,'browser_download_url':prefix+name} for name in names]}
        value=update.parse_release(data,'0.3.1')
        self.assertEqual(value.name,names[1]);self.assertEqual(value.kind,'setup')

    def test_bundle_copy_never_copies_data(self):
        (self.root/'AIClockIn.exe').write_bytes(b'exe')
        runtime=self.root/'_runtime-v0.4.0';runtime.mkdir();(runtime/'python.dll').write_bytes(b'dll')
        (self.root/'data').mkdir();(self.root/'data/accounts.json').write_text('private')
        package.write_manifest(self.root,'0.4.0')
        dest=self.root/'snapshot'
        package.copy_bundle(self.root,dest)
        self.assertTrue((dest/'AIClockIn.exe').exists());self.assertFalse((dest/'data').exists())

    def test_inno_script_has_no_data_delete_and_dependencies_first(self):
        script=(Path(__file__).resolve().parent.parent/'installer/AIClockIn.iss').read_text('utf-8-sig')
        self.assertIn('PrivilegesRequired=lowest',script)
        self.assertIn('Uninstallable=yes',script)
        self.assertNotIn('[UninstallDelete]',script)
        self.assertLess(script.index('Source: "{#BundleDir}\\{#RuntimeDir}\\*"'),script.index('Source: "{#BundleDir}\\AIClockIn.exe"'))

    def test_uninstall_never_removes_other_installations_task(self):
        from aiclockin.setup_support import remove_own_task
        from aiclockin.schedule import definition
        from unittest.mock import Mock
        exe=self.root/'AIClockIn.exe';data=self.root/'data'
        backend=Mock();backend.user='synthetic-user'
        backend.get.return_value=definition(self.root/'other/AIClockIn.exe',backend.user,data)
        self.assertEqual(remove_own_task(exe,data,backend),0)
        backend.remove.assert_not_called()
        backend.get.side_effect=[definition(exe,backend.user,data),None]
        self.assertEqual(remove_own_task(exe,data,backend),0)
        backend.remove.assert_called_once()

    def test_uninstall_refuses_wrong_account_or_data(self):
        from aiclockin.setup_support import remove_own_task
        from aiclockin.schedule import definition
        from unittest.mock import Mock
        exe=self.root/'AIClockIn.exe';data=self.root/'data';backend=Mock();backend.user='current-user'
        backend.get.return_value=definition(exe,'other-user',data)
        with self.assertRaises(RuntimeError):remove_own_task(exe,data,backend)
        backend.remove.assert_not_called()


if __name__=='__main__':unittest.main()
