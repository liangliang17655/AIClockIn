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
                self.assertEqual(len(app.accounts.get_children()), 2)
                self.assertIn('账号身份待确认', app.accounts.item('doubaowork-current-session', 'values')[1])
                self.assertEqual(len(app.history.get_children()), 1)
                self.assertNotIn('private-token', str(app.accounts.item('a', 'values')))
                self.assertIn('示例账号', app.accounts.item('a', 'values'))
                app.accounts.selection_set('doubaowork-current-session')
                app.query()
                root.update()
                dialog = app.doubao_window
                self.assertEqual(dialog.values['binding'].get(), '账号身份待确认')
                self.assertEqual(dialog.values['checkin'].get(), '状态未知')
                app.toggle()
                self.assertEqual(store.accounts()[0]['id'], 'a')
                self.assertEqual(len(store.accounts()), 1)
                dialog.close()
            finally:
                root.destroy()


if __name__ == '__main__':
    unittest.main()
