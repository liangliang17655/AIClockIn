from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
from unittest.mock import patch
import tempfile
import unittest
from tools.sample_doubao_day import validate_day, reserve_output


class DaySampleTests(unittest.TestCase):
    def test_wrong_day_cannot_be_used_as_next_day_sample(self):
        with self.assertRaises(ValueError):
            validate_day('2026-11-16', datetime(2026,11,15,23,59,tzinfo=timezone(timedelta(hours=8))))

    def test_timezone_is_beijing_not_host_timezone(self):
        validate_day('2026-11-16',datetime(2026,11,15,16,5,tzinfo=timezone.utc))

    def test_existing_evidence_is_never_overwritten(self):
        root=Path('D:/个人开发软件/AI工作区/temp/AIClockIn-tests');root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as folder:
            output=Path(folder)/'sample';reserve_output(output)
            marker=output/'manifest.json';marker.write_text('keep','utf-8')
            with self.assertRaises(FileExistsError):reserve_output(output)
            self.assertEqual(marker.read_text('utf-8'),'keep')

    def test_wrong_day_cli_keeps_failure_without_opening_data(self):
        from datetime import timedelta
        from tools.sample_doubao_day import main, ZONE
        root=Path('D:/个人开发软件/AI工作区/temp/AIClockIn-tests')
        with tempfile.TemporaryDirectory(dir=root) as folder:
            output=Path(folder)/'failed';data=Path(folder)/'untouched-data'
            future=(datetime.now(ZONE)+timedelta(days=1)).date().isoformat()
            with patch('sys.argv',['sample','--day',future,'--data',str(data),'--out',str(output)]):
                self.assertEqual(main(),1)
            self.assertFalse(data.exists())
            self.assertEqual(json.loads((output/'manifest.json').read_text('utf-8'))['status'],'failed')
