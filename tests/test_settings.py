from pathlib import Path
import tempfile
import threading
import time
import tkinter as tk
import unittest
from unittest.mock import patch

from aiclockin.gui import App
from aiclockin.store import Store
from aiclockin.runtime import TEMP


class SettingsTests(unittest.TestCase):
    def setUp(self):
        TEMP.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=TEMP)
        self.root=tk.Tk()
        self.app=App(self.root,Store(Path(self.temp.name)),check_updates=False)
        self.root.update()

    def tearDown(self):
        self.root.destroy();self.temp.cleanup()

    def drain(self):
        time.sleep(.03);self.app.poll();self.root.update()

    def test_settings_panel_toggle_keyboard_and_outside_close(self):
        menu=self.app.updates.menu
        self.app.updates.button.invoke();self.root.update()
        self.assertTrue(menu.window.winfo_ismapped())
        self.assertEqual([b['text'] for b in menu.actions],['检查更新','自动检查更新','创建桌面快捷方式','关于软件'])
        menu.window.event_generate('<Escape>');self.root.update()
        self.assertIsNone(menu.window)

    def test_keyboard_can_toggle_and_close_panel(self):
        self.app.updates.button.invoke();self.root.update()
        menu=self.app.updates.menu
        menu.shift(1);self.root.update()
        self.assertEqual(self.root.focus_get(),menu.actions[0])
        menu.shift(1);self.root.update()
        menu.actions[1].event_generate('<Return>');self.root.update()
        self.assertFalse(self.app.updates.auto.get())
        menu.window.event_generate('<Escape>');self.root.update()
        self.assertIsNone(menu.window)
        self.app.updates.button.invoke();self.root.update()
        self.app.accounts.event_generate('<Button-1>',x=5,y=5);self.root.update()
        self.assertIsNone(menu.window)

    def test_toggle_persists_without_losing_running_operation(self):
        self.app.running=True
        self.app.updates.button.invoke();self.root.update()
        self.app.updates.menu.actions[1].invoke();self.root.update()
        self.assertFalse(self.app.updates.auto.get())
        self.assertTrue((Path(self.temp.name)/'update-settings.json').exists())
        self.assertTrue(self.app.running)

    def test_shortcut_is_direct_async_and_reports_success(self):
        self.app.running=True
        with patch('aiclockin.update_gui.sys.frozen',True,create=True), \
             patch('aiclockin.update_gui.create_shortcut',return_value='desktop/AIClockIn.lnk') as create, \
             patch.object(self.app,'worker') as worker, \
             patch('aiclockin.update_gui.messagebox.showinfo') as info:
            self.app.updates.desktop_shortcut();self.drain()
            create.assert_called_once()
            worker.assert_not_called()
            info.assert_called_once()
        self.assertTrue(self.app.running)

    def test_shortcut_failure_is_visible_and_retry_allowed(self):
        with patch('aiclockin.update_gui.sys.frozen',True,create=True), \
             patch('aiclockin.update_gui.create_shortcut',side_effect=RuntimeError('denied')), \
             patch('aiclockin.update_gui.messagebox.showerror') as error:
            self.app.updates.desktop_shortcut();self.drain()
            self.assertFalse(self.app.updates.creating_shortcut)
            error.assert_called_once()


if __name__=='__main__':unittest.main()
