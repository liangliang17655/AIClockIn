from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
try:
    from aiclockin.schedule import TaskManager
except ImportError:
    TaskManager = None


class Tasks:
    user = 'S-1-5-21-test'
    def __init__(self):
        self.xml = None
        self.raise_after_put = False
    def get(self):
        return self.xml
    def put(self, xml):
        self.xml = xml
        if self.raise_after_put:
            raise RuntimeError('transport lost')
    def remove(self):
        self.xml = None


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(TaskManager, '独立自动任务未实现')
        self.temp = tempfile.TemporaryDirectory(dir='D:/个人开发软件/AI工作区/temp/AIClockIn-tests')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exe = self.root / 'AIClockIn.exe'
        self.exe.write_bytes(b'test')
        self.tasks = Tasks()
        self.manager = TaskManager(self.root, self.exe, self.tasks)

    def test_enabled_task_calls_absolute_exe_without_gui(self):
        self.manager.enable()
        self.assertTrue(self.manager.status()['enabled'])
        ns = {'t': 'http://schemas.microsoft.com/windows/2004/02/mit/task'}
        root = ET.fromstring(self.tasks.xml)
        self.assertEqual(root.findtext('t:Actions/t:Exec/t:Command', namespaces=ns), str(self.exe))
        self.assertEqual(root.findtext('t:Actions/t:Exec/t:Arguments', namespaces=ns), '--silent --data ' + str(self.root))
        self.assertEqual(root.findtext('t:Principals/t:Principal/t:LogonType', namespaces=ns), 'InteractiveToken')
        self.assertEqual(len(root.find('t:Triggers', ns)), 8)

    def test_registration_after_commit_failure_restores_absence(self):
        self.tasks.raise_after_put = True
        with self.assertRaises(RuntimeError):
            self.manager.enable()
        self.assertIsNone(self.tasks.xml)

    def test_disable_and_missing_state(self):
        self.manager.enable()
        self.manager.disable()
        self.assertFalse(self.manager.status()['enabled'])

    def test_custom_data_directory_is_retained_by_background_task(self):
        data = self.root / 'custom-data'
        manager = TaskManager(data, self.exe, self.tasks)
        manager.enable()
        ns = {'t': 'http://schemas.microsoft.com/windows/2004/02/mit/task'}
        xml = ET.fromstring(self.tasks.xml)
        arguments = xml.findtext('t:Actions/t:Exec/t:Arguments', namespaces=ns)
        self.assertIn('--data', arguments)
        self.assertIn(str(data), arguments)


if __name__ == '__main__':
    unittest.main()
