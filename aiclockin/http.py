"""Small standard-library HTTP client; never logs requests or credentials."""
import json
import socket
import time
import urllib.error
import urllib.request


class RequestFailure(RuntimeError):
    pass


class HTTP:
    def post(self, url, headers, body):
        request = urllib.request.Request(url, json.dumps(body).encode('utf-8'),
            {'Content-Type': 'application/json', **headers}, method='POST')
        can_retry = not (url.endswith('/claim') or url.endswith('/daily-checkin'))
        for attempt in range(2 if can_retry else 1):
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    payload = json.loads(response.read().decode('utf-8'))
                    if not isinstance(payload, dict):
                        raise RequestFailure('接口响应不是 JSON 对象')
                    return payload
            except urllib.error.HTTPError as exc:
                if can_retry and attempt == 0 and exc.code in (429, 500, 502, 503, 504):
                    time.sleep(1)
                    continue
                raise RequestFailure(f'接口 HTTP {exc.code}') from None
            except (urllib.error.URLError, TimeoutError, socket.timeout):
                if can_retry and attempt == 0:
                    time.sleep(1)
                    continue
                raise RequestFailure('网络不可用或接口超时') from None
            except (UnicodeError, json.JSONDecodeError):
                raise RequestFailure('接口返回内容无法解析') from None
