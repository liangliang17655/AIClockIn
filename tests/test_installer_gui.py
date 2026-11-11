from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from aiclockin.installer import InstallerUI, DEFAULT
from aiclockin.runtime import TEMP


class InstallerGuiTests(unittest.TestCase):
    def setUp(self):
        TEMP.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=TEMP)
        self.source = Path(self.tmp.name) / 'AIClockIn.exe'
        self.source.write_bytes(b'test')
        self.root = tk.Tk(); self.root.withdraw()

    def tearDown(self):
        for job in self.root.tk.call('after', 'info'):
            self.root.after_cancel(job)
        self.root.destroy(); self.tmp.cleanup()

    def test_first_install_default_and_minimum_button_visible(self):
        with patch('aiclockin.installer.location', return_value=(DEFAULT, DEFAULT/'data', False)):
            app = InstallerUI(self.root, self.source)
        self.root.deiconify(); self.root.geometry('560x340'); self.root.update()
        self.assertEqual(Path(app.path.get()), DEFAULT)
        self.assertTrue(app.action.winfo_ismapped())
        self.assertLessEqual(app.action.winfo_rooty()+app.action.winfo_height(), self.root.winfo_rooty()+self.root.winfo_height())
        app.path.set('C:/Users/test/Desktop'); app.begin()
        self.assertIn('D 盘', app.status.get()); self.assertFalse(app.busy)

    def test_existing_location_locked_and_failure_can_retry(self):
        data = self.source.parent / 'custom data'
        app = InstallerUI(self.root, self.source, data)
        self.assertEqual(str(app.entry['state']), 'readonly')
        self.assertEqual(str(app.browse['state']), 'disabled')
        app.busy = True
        app.events.put((None, data, '创建失败'))
        app.poll()
        self.assertFalse(app.busy)
        self.assertEqual(str(app.action['state']), 'normal')
        self.assertIn('创建失败', app.status.get())

    def test_settings_shortcut_completion_does_not_open_another_gui(self):
        data = self.source.parent/'data'
        app = InstallerUI(self.root, self.source, data)
        with patch.object(app, 'open_app') as opened, patch.object(app, 'close') as closed:
            app.events.put((self.source, data, None)); app.poll(); app.action.invoke()
            closed.assert_called_once()
            opened.assert_not_called()


if __name__ == '__main__':
    unittest.main()
