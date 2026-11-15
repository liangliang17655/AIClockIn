import tempfile
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
import unittest
from unittest.mock import patch

from aiclockin.store import Store
from aiclockin.doubao_gui import QuotaWindow


class BindingGuiTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(dir='D:/个人开发软件/AI工作区/temp/AIClockIn-tests')
        self.addCleanup(folder.cleanup)
        self.root = tk.Tk(); self.root.withdraw()
        self.addCleanup(self.root.destroy)
        app = SimpleNamespace(root=self.root, store=Store(folder.name), running=False,
                              updating=False, refresh=lambda: None)
        self.dialog = QuotaWindow(app)
        self.dialog.window.update_idletasks()

    def test_cancel_confirmation_writes_no_binding(self):
        self.dialog.events.put(('binding_candidate', 'a'*64))
        with patch('aiclockin.doubao_gui.messagebox.askyesno', return_value=False):
            self.dialog.poll()
        self.assertFalse((self.dialog.app.store.root/'doubao-binding.json').exists())
        self.assertFalse(self.dialog.busy)

    def test_binding_controls_fit_small_window(self):
        self.dialog.window.geometry('570x580'); self.dialog.window.update_idletasks()
        for button in (self.dialog.bind_button, self.dialog.check_button):
            bottom = button.winfo_rooty() - self.dialog.window.winfo_rooty() + button.winfo_height()
            self.assertLessEqual(bottom, self.dialog.window.winfo_height())
