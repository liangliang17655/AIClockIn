import unittest
from aiclockin.doubao_receipt import verify_delivery


class DeliveryTests(unittest.TestCase):
    def ledger(self, rows): return {'header_verified': True, 'snapshot_complete': True, 'rows': rows}
    def attempt(self):
        return {'before_identity': 'a'*64, 'after_identity': 'a'*64,
                'started_at': '2026-11-16T00:05:20+08:00',
                'observed_at': '2026-11-16T00:05:40+08:00'}
    def row(self): return {'task':'每日签到','time':'2026-11-16 00:05','earned':200}

    def test_new_dated_official_row_confirms_delivery(self):
        result=verify_delivery(self.ledger([]),self.ledger([self.row()]),self.attempt())
        self.assertEqual(result['state'],'confirmed')
        self.assertEqual(result['earned'],200)
        self.assertIsNone(result['remaining'])

    def test_existing_receipt_is_not_this_attempt(self):
        result=verify_delivery(self.ledger([self.row()]),self.ledger([self.row()]),self.attempt())
        self.assertEqual(result['state'],'unknown')

    def test_header_alone_does_not_prove_complete_before_snapshot(self):
        before=self.ledger([]);before.pop('snapshot_complete')
        self.assertEqual(verify_delivery(before,self.ledger([self.row()]),self.attempt())['state'],'unknown')

    def test_missing_before_or_identity_mismatch_stops(self):
        self.assertEqual(verify_delivery({},self.ledger([self.row()]),self.attempt())['state'],'unknown')
        attempt=self.attempt();attempt['after_identity']='b'*64
        self.assertEqual(verify_delivery(self.ledger([]),self.ledger([self.row()]),attempt)['state'],'unknown')

    def test_duplicate_or_old_or_unrelated_rows_do_not_confirm(self):
        for rows in ([self.row(), self.row()], [{'task':'每日签到','time':'2026-11-15 00:05','earned':200}],
                     [{'task':'其他任务','time':'2026-11-16 00:05','earned':200}]):
            self.assertEqual(verify_delivery(self.ledger([]),self.ledger(rows),self.attempt())['state'],'unknown')
