from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from aiclockin.store import Store
try:
    from aiclockin.gui import App
except ImportError:
    App = None


class GuiTest(unittest.TestCase):
    def test_encrypted_account_and_failure_history_render(self):
        self.assertIsNotNone(App, '全新界面尚未实现')
        with tempfile.TemporaryDirectory(dir='D:/个人开发软件/AI工作区/temp/AIClockIn-tests') as folder:
            store = Store(Path(folder))
            store.save_accounts([{'id': 'a', 'name': '示例账号', 'platform': 'workbuddy', 'enabled': True,
                                  'credentials': {'uid': 'private-uid', 'access_token': 'private-token'}}])
            store.record('a', 'workbuddy', '示例账号', '失败', None, None, '接口超时')
            root = tk.Tk()
            root.withdraw()
            try:
                app = App(root, store)
                root.update()
                self.assertEqual(len(app.accounts.get_children()), 1)
                self.assertEqual(len(app.history.get_children()), 1)
                self.assertNotIn('private-token', str(app.accounts.item('a', 'values')))
                self.assertIn('示例账号', app.accounts.item('a', 'values'))
            finally:
                root.destroy()


if __name__ == '__main__':
    unittest.main()
