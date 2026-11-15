"""One bounded activity/official-ledger candidate bundle. Never submits a claim."""
import argparse
from datetime import date, datetime, timezone, timedelta
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aiclockin.doubao_binding import load, read_candidate
from aiclockin.doubao_receipt import classify
from aiclockin.doubao_session import ClientBackend, check_bound_session
from aiclockin.store import Store, OperationLock, write_json
from tools.doubao_compare import capture
from tools.probe_doubao_signin import capture as reveal_capture

ZONE = timezone(timedelta(hours=8))


def validate_day(day, now=None):
    day = date.fromisoformat(day)
    now = now or datetime.now(ZONE)
    if now.tzinfo is None or now.astimezone(ZONE).date() != day:
        raise ValueError('capture_day_mismatch')


def reserve_output(output):
    output = output.resolve()
    if output.drive.upper() != 'D:':
        raise ValueError('output_requires_D_drive')
    output.mkdir(parents=True, exist_ok=False)


def sample(store, day, output, label):
    validate_day(day)
    output = output.resolve(); reserve_output(output)
    manifest = {'target_day': day, 'started_at': datetime.now(ZONE).isoformat(),
                'label': label, 'status': 'started', 'phase': 'preflight',
                'bundle_complete': False, 'unclaimed_proven': False,
                'claim_attempted': False, 'business_date_confirmed': False}
    write_json(output/'manifest.json', manifest)
    backend = ClientBackend(); ledger_open = False
    try:
        result = check_bound_session(store, backend)
        manifest['preflight'] = result
        if not result.get('query_completed'):
            raise ValueError('bound_preflight_incomplete')
        with OperationLock(store.root):
            bound = load(store)
            if not bound or read_candidate(backend) != bound['fingerprint']:
                raise ValueError('identity_mismatch_before_sample')
            manifest['binding_id'] = bound['id']
            manifest['phase'] = 'activity'; write_json(output/'manifest.json', manifest)
            if not backend.inspect(90).get('activity_ready'):
                raise ValueError('activity_unavailable')
            manifest['refresh'] = backend.refresh_activity()
            reveal_capture(navigate=False, restore=False, reveal=True)
            activity = capture(output/'activity.json', label+'-activity', passive=True)
            manifest['phase'] = 'ledger'; write_json(output/'manifest.json', manifest)
            ledger_open = True
            ledger = backend.inspect_ledger(keep_open=True)
            raw = capture(output/'ledger-uia.json', label+'-ledger', passive=True)
            closed = backend.close_ledger().get('closed') is True
            ledger_open = not closed
            ledger['dialog_closed'] = closed
            # Completeness of absence/pagination is not established by a table header.
            ledger['snapshot_complete'] = False
            write_json(output/'ledger.json', ledger)
            manifest['phase'] = 'identity_recheck'; write_json(output/'manifest.json', manifest)
            if read_candidate(backend) != bound['fingerprint']:
                raise ValueError('identity_mismatch_after_sample')
            manifest['identity_matched'] = True
            returned = backend.inspect(90).get('activity_ready') is True
            validate_day(day)
            if not backend.desktop_status()[0]:
                raise ValueError('desktop_unavailable')
            ledger_window_captured = any(n.get('type') == 'ControlType.Window' and n.get('name') == '奖励发放明细'
                for doc in raw.get('documents',[]) for n in doc.get('tree',[]))
            manifest['official_receipt'] = classify(ledger,day)
            manifest['business_date_confirmed'] = manifest['official_receipt']['state'] == 'already_signed'
            manifest['bundle_complete'] = bool(activity.get('evidence_complete') and raw.get('evidence_complete')
                and ledger.get('header_verified') and ledger_window_captured and closed and returned)
            manifest['status'] = 'candidate_saved' if manifest['bundle_complete'] else 'incomplete'
    except Exception as exc:
        manifest['status'] = 'failed'
        manifest['error_type'] = type(exc).__name__
        # Only controlled reason codes; no client/credential exception strings.
        reasons = {'capture_day_mismatch','bound_preflight_incomplete','identity_mismatch_before_sample',
                   'identity_mismatch_after_sample','activity_unavailable','desktop_unavailable'}
        manifest['reason'] = str(exc) if type(exc) is ValueError and str(exc) in reasons else 'sample_failed'
    finally:
        if ledger_open:
            try: manifest['cleanup_closed_ledger'] = backend.close_ledger().get('closed') is True
            except Exception: manifest['cleanup_closed_ledger'] = False
        manifest['finished_at'] = datetime.now(ZONE).isoformat()
        write_json(output/'manifest.json',manifest)
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--day',required=True)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--label',default='next-day-candidate-unverified')
    args=parser.parse_args()
    try:
        validate_day(args.day)
    except ValueError:
        reserve_output(args.out)
        write_json(args.out/'manifest.json', {'status':'failed','reason':'capture_day_mismatch',
            'target_day':args.day,'observed_at':datetime.now(ZONE).isoformat(),
            'bundle_complete':False,'claim_attempted':False,'unclaimed_proven':False})
        return 1
    result=sample(Store(args.data),args.day,args.out,args.label)
    if sys.stdout is not None:
        print(json.dumps({'status':result['status'],'bundle_complete':result['bundle_complete'],
                          'unclaimed_proven':False,'claim_attempted':False},ensure_ascii=True))
    return 0 if result['bundle_complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
