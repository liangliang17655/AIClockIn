"""Opt-in official settings UIA inspection. No login/claim/account changes."""
import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aiclockin.doubao_session import ClientBackend


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.resolve().drive.upper() != 'D:':
        parser.error('Output must be on D:')
    if args.out.exists():
        parser.error('Refusing to overwrite evidence')
    backend = ClientBackend()
    if not backend.desktop_status()[0] or not backend.running():
        parser.error('An unlocked desktop and running official client are required')
    first, second = backend.inspect_identity(), backend.inspect_identity()
    result = {'captured_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'observations': [first, second], 'identity_verified': False,
              'same_visible_number': bool(first.get('account_fingerprint') and
                   first.get('account_fingerprint') == second.get('account_fingerprint')),
              'claim_attempted': False}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()
