"""Audit real capture evidence without promoting capture dates to business dates."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re


def inspect_sample(data):
    docs = data.get('documents', [])
    valid = bool(data.get('capture_ok') and len(docs) == 1 and
                 docs[0].get('tree') and not docs[0].get('tree_truncated'))
    nodes = docs[0].get('tree', []) if valid else []
    buttons = [n for n in nodes if n.get('type') == 'ControlType.Button'
               and n.get('name') == '立即签到' and n.get('enabled') is True
               and n.get('offscreen') is False
               and 'InvokePatternIdentifiers.Pattern' in n.get('patterns', [])]
    # Only report date-bearing node evidence; this does not assign its semantics.
    dates = []
    for node in nodes:
        for field in ('name', 'help', 'status'):
            value = node.get(field, '')
            if re.search(r'20\d{2}[-年/]\d{1,2}[-月/]\d{1,2}', value):
                dates.append({'path': node.get('path'), 'field': field})
    return {'valid_capture': valid, 'node_count': len(nodes),
            'claim_button_count': len(buttons),
            'success_toast_visible': any(n.get('type') == 'ControlType.Text'
                and n.get('name') == '签到成功' and n.get('offscreen') is False for n in nodes),
            'date_bearing_nodes': dates,
            'business_date_observed': False,  # No validated date semantics in current captures.
            'identity_verified': data.get('identity_verified') is True,
            'daily_state': 'unknown', 'captured_at': data.get('captured_at')}


def audit(folder):
    result = {}
    for label, filename in [('before', 'auto-once-before.json'),
                            ('after', 'auto-once-after-001.json')]:
        raw = (folder / filename).read_bytes()
        result[label] = inspect_sample(json.loads(raw.decode('utf-8-sig')))
        result[label]['sha256'] = hashlib.sha256(raw).hexdigest()
    attempt = json.loads((folder / 'auto-once-attempt.json').read_text('utf-8-sig'))
    before, after = result['before'], result['after']
    ordered = False
    try:
        start, submitted, end = [datetime.fromisoformat(x) for x in
            (before['captured_at'], attempt['time'], after['captured_at'])]
        ordered = start <= submitted <= end and (end - submitted).total_seconds() <= 60
    except (ValueError, KeyError, TypeError):
        pass
    result['ordered_single_claim_transition_observed'] = bool(
        before['valid_capture'] and after['valid_capture'] and ordered
        and attempt.get('max_invocations') == 1 and attempt.get('phase') == 'invoke_returned'
        and before['claim_button_count'] == 1 and after['claim_button_count'] == 0
        and after['success_toast_visible'])
    result['current_account_daily_state'] = 'unknown'
    result['limitations'] = ['identity_unverified', 'business_date_missing', 'toast_is_transient']
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.resolve().drive.upper() != 'D:':
        parser.error('Output must be on D:')
    result = audit(args.samples)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()
