"""Opt-in live identity versus synthetic mismatched binding; no real account switch."""
import hashlib
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aiclockin.doubao_binding import confirm, read_candidate
from aiclockin.doubao_session import ClientBackend, check_bound_session
from aiclockin.package import data_root
from aiclockin.runtime import home
from aiclockin.store import Store


class LiveGuard(ClientBackend):
    navigation_calls = 0
    def inspect(self, timeout):
        self.navigation_calls += 1
        raise AssertionError('Mismatch must stop before navigation')


def main():
    real = LiveGuard()
    current = read_candidate(real)
    wrong = '0' * 64 if current != '0' * 64 else '1' * 64
    class SyntheticFixture:
        def desktop_status(self): return True, 0
        def running(self): return True
        def inspect_identity(self): return {'account_fingerprint': wrong}
    output = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/task027') / ('mismatch-' + uuid.uuid4().hex[:12])
    store = Store(output / 'data')
    # This confirmation is synthetic test input, not a user-confirmed real account.
    confirm(store, wrong, SyntheticFixture(), confirmed=True)
    protected = data_root(home())
    def hashes():
        return {name: hashlib.sha256((protected/name).read_bytes()).hexdigest()
                for name in ('accounts.json','history.db','doubao-binding.json') if (protected/name).exists()}
    before = hashes()
    result = check_bound_session(store, real)
    assert result['reason'] == 'account_mismatch', result
    assert real.navigation_calls == 0 and result['claim_attempted'] is False
    summary = {'synthetic_binding_fixture': True, 'live_identity_read': True,
               'actual_account_switch_tested': False, 'result': result,
               'navigation_calls': real.navigation_calls, 'production_files_unchanged': before == hashes()}
    (output / 'result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), 'utf-8')
    print(str(output / 'result.json'))
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == '__main__':
    main()
