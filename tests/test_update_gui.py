from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch
import time

from aiclockin.store import Store
from aiclockin.gui import App
from aiclockin.update import Release, ROOT, UpdateError


class UpdateGuiTests(unittest.TestCase):
    def setUp(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.root = tk.Tk(); self.root.withdraw()
        self.app = App(self.root, Store(Path(self.temp.name)), check_updates=False)

    def tearDown(self):
        self.root.destroy(); self.temp.cleanup()

    def drain(self):
        time.sleep(0.03)
        self.app.poll()
        self.root.update()

    def test_menu_manual_latest_and_busy_is_not_cleared(self):
        self.assertIn('检查更新', [row[0] for row in self.app.updates.menu.rows])
        self.app.running = True
        with patch('aiclockin.update_gui.check', return_value=None), patch('aiclockin.update_gui.messagebox.showinfo') as info:
            self.app.updates.check(True)
            self.drain()
            info.assert_called_once()
        self.assertTrue(self.app.running)

    def test_startup_silent_and_network_error_retry(self):
        with patch('aiclockin.update_gui.check', return_value=None), patch('aiclockin.update_gui.messagebox.showinfo') as info:
            self.app.updates.check(False); self.drain(); info.assert_not_called()
        with patch('aiclockin.update_gui.check', side_effect=UpdateError('网络失败')), \
             patch('aiclockin.update_gui.messagebox.askretrycancel', return_value=False) as retry:
            self.app.updates.check(True); self.drain(); retry.assert_called_once()
        self.assertFalse(self.app.updates.checking)

    def test_remote_notes_and_progress(self):
        item = Release('v0.2.0', '远程发布说明\n修复例子', 'name.exe', '', 100, None, None)
        self.app.updates.show_release(item)
        self.assertIn('远程发布说明', self.app.updates.notes.get('1.0', 'end'))
        self.app.updates.handle('progress', (30, 100))
        self.assertEqual(float(self.app.updates.progress['value']), 30)

    def test_later_update_closes_without_using_release_local(self):
        self.app.updates.show_release(Release('v0.4.0','说明','name.exe','',1,None,None))
        self.app.updates.close_dialog()
        self.assertIsNone(self.app.updates.dialog)

    def test_update_actions_remain_visible_at_minimum_size(self):
        self.root.deiconify()
        self.app.updates.show_release(Release('v0.2.1', '说明\n' * 80, '', '', 1, None, None))
        self.app.updates.dialog.geometry('480x380')
        self.root.update()
        button = self.app.updates.install_button
        self.assertTrue(button.winfo_ismapped())
        self.assertLessEqual(button.winfo_rooty() + button.winfo_height(),
                             self.app.updates.dialog.winfo_rooty() + self.app.updates.dialog.winfo_height())

    def test_startup_schedules_check_and_toggle_persists(self):
        from aiclockin.update_gui import UpdateUI
        header = tk.Frame(self.root)
        updates = UpdateUI(self.app, header)
        self.assertIsNotNone(updates.startup_job)
        with patch.object(updates, 'check') as check:
            self.root.tk.call('eval', self.root.tk.call('after', 'info', updates.startup_job)[0])
            check.assert_called_once_with(False)
        self.root.after_cancel(updates.startup_job)
        updates.auto.set(False); updates.save_settings()
        another = UpdateUI(self.app, header)
        self.assertFalse(another.auto.get())
        self.assertIsNone(another.startup_job)


if __name__ == '__main__':
    unittest.main()
