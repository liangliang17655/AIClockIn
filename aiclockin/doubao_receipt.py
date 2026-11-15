"""Only a dated official daily-task reward proves an already-claimed state."""
from datetime import datetime, timedelta, timezone
import re


def classify(ledger, day):
    result = {'state': 'unknown', 'official_reward': None, 'official_time': None}
    if ledger.get('header_verified') is not True or ledger.get('dialog_closed') is not True:
        return result
    matches = []
    for row in ledger.get('rows', []):
        try:
            stamp = datetime.strptime(row['time'], '%Y-%m-%d %H:%M')
            if (row.get('task') == '每日签到' and stamp.date().isoformat() == day
                and type(row.get('earned')) is int and 0 < row['earned'] < 10**9):
                matches.append(row)
        except (KeyError, ValueError, TypeError):
            continue
    if len(matches) == 1:
        result.update(state='already_signed', official_reward=matches[0]['earned'], official_time=matches[0]['time'])
    return result


def verify_delivery(before, after, attempt):
    """Evidence gate only, no submission. Header/empty table is not complete evidence."""
    result = {'state': 'unknown', 'earned': None, 'remaining': None}
    for ledger in (before, after):
        if (ledger.get('header_verified') is not True or ledger.get('snapshot_complete') is not True
            or not isinstance(ledger.get('rows'), list)):
            return result
    identity = attempt.get('before_identity')
    if (not isinstance(identity, str) or not re.fullmatch(r'[0-9a-f]{64}', identity)
        or identity != attempt.get('after_identity')):
        return result
    try:
        start, end = [datetime.fromisoformat(attempt[key]) for key in ('started_at','observed_at')]
        if start.tzinfo is None or end.tzinfo is None or not 0 <= (end-start).total_seconds() <= 600:
            return result
        zone = timezone(timedelta(hours=8))
        start, end = start.astimezone(zone), end.astimezone(zone)
        if start.date() != end.date():
            return result
        def key(row):
            if not isinstance(row, dict): return None
            if row.get('task') != '每日签到' or type(row.get('earned')) is not int or row['earned'] <= 0:
                return None
            stamp = datetime.strptime(row['time'], '%Y-%m-%d %H:%M').replace(tzinfo=zone)
            return stamp, row['earned']
        old = {key(row) for row in before['rows']}
        fresh = [key(row) for row in after['rows']]
        fresh = [item for item in fresh if item and item not in old
                 and start.replace(second=0,microsecond=0) <= item[0] <= end]
        if len(fresh) == 1:
            result.update(state='confirmed', earned=fresh[0][1], official_time=fresh[0][0].strftime('%Y-%m-%d %H:%M'),
                          official_time_precision='minute', submission_time=start.isoformat())
    except (ValueError, TypeError, KeyError, OverflowError):
        pass
    return result
