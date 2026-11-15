"""Comparison guard tests only. These fixtures are not real sign-in evidence."""
import unittest
from tools.doubao_compare import compare


def fixture(kind='ControlType.Text'):
    return {'capture_ok': True, 'beijing_day': '2026-11-15', 'captured_at': '2026-11-15T00:05:00+08:00',
            'documents': [{'text': '累计获得额度：\n200\n点', 'tree': [
                {'path': '0', 'name': '立即签到', 'type': kind, 'patterns': ['InvokePatternIdentifiers.Pattern']}]}]}


class CompareGuards(unittest.TestCase):
    def test_group_and_text_are_never_buttons_even_with_invoke_pattern(self):
        for kind in ('ControlType.Group', 'ControlType.Text'):
            data = fixture(kind)
            self.assertEqual(compare(data, data)['before_button_candidates'], [])

    def test_even_a_button_is_only_a_candidate_not_verified_state(self):
        data = fixture('ControlType.Button')
        result = compare(data, data)
        self.assertEqual(len(result['before_button_candidates']), 1)
        self.assertEqual(result['sign_state'], 'unknown')
        self.assertFalse(result['receipt_verified'])
        self.assertIsNone(result['earned'])

    def test_missing_wrong_day_or_reverse_time_pair_is_rejected(self):
        for altered in ({'capture_ok': False}, {'beijing_day': '2026-11-16'},
                        {'captured_at': '2026-11-14T23:59:00+08:00'}):
            after = {**fixture(), **altered}
            self.assertFalse(compare(fixture(), after)['usable_pair'])


if __name__ == '__main__':
    unittest.main()
