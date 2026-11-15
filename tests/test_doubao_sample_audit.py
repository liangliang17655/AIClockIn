import unittest
from tools.audit_doubao_samples import inspect_sample


class AuditTests(unittest.TestCase):
    def sample(self, node):
        return {'capture_ok': True, 'identity_verified': False, 'beijing_day': '2026-11-15',
                'documents': [{'tree_truncated': False, 'tree': [node]}]}

    def test_capture_date_is_not_business_date(self):
        result = inspect_sample(self.sample({'type': 'ControlType.Text', 'name': '累计获得额度：400'}))
        self.assertEqual(result['daily_state'], 'unknown')
        self.assertFalse(result['business_date_observed'])

    def test_group_is_not_claim_button(self):
        result = inspect_sample(self.sample({'type': 'ControlType.Group', 'name': '立即签到',
            'enabled': True, 'offscreen': False, 'patterns': ['InvokePatternIdentifiers.Pattern']}))
        self.assertEqual(result['claim_button_count'], 0)

    def test_real_button_without_date_is_only_candidate(self):
        result = inspect_sample(self.sample({'type': 'ControlType.Button', 'name': '立即签到',
            'enabled': True, 'offscreen': False, 'patterns': ['InvokePatternIdentifiers.Pattern']}))
        self.assertEqual(result['claim_button_count'], 1)
        self.assertEqual(result['daily_state'], 'unknown')

    def test_failed_capture_cannot_supply_evidence(self):
        self.assertFalse(inspect_sample({'capture_ok': False, 'documents': []})['valid_capture'])


if __name__ == '__main__':
    unittest.main()
