import unittest
from aiclockin.doubao_receipt import classify


class ReceiptTests(unittest.TestCase):
    def receipt(self, rows): return {'header_verified': True, 'dialog_closed': True, 'rows': rows}
    def row(self, **changes):
        value = {'task': '每日签到', 'time': '2026-11-15 00:23', 'earned': 200}
        value.update(changes); return value

    def test_dated_daily_reward_proves_already_signed(self):
        result = classify(self.receipt([self.row()]), '2026-11-15')
        self.assertEqual(result['state'], 'already_signed')
        self.assertEqual(result['official_reward'], 200)

    def test_absence_or_other_day_does_not_prove_unsigned(self):
        for rows in ([], [self.row(time='2026-11-14 00:23')]):
            self.assertEqual(classify(self.receipt(rows), '2026-11-15')['state'], 'unknown')

    def test_other_task_or_invalid_amount_is_not_signin(self):
        for row in (self.row(task='选择工作领域'), self.row(earned=0), self.row(earned=True), self.row(time='not-a-date')):
            self.assertEqual(classify(self.receipt([row]), '2026-11-15')['state'], 'unknown')

    def test_duplicate_rows_and_changed_header_stop(self):
        result = classify(self.receipt([self.row(),self.row()]), '2026-11-15')
        self.assertEqual(result['state'], 'unknown')
        result = self.receipt([self.row()]);result['header_verified'] = False
        self.assertEqual(classify(result, '2026-11-15')['state'], 'unknown')
