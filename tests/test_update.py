import hashlib
import io
import tempfile
from pathlib import Path
import unittest
import threading
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from aiclockin import update as u


def release(version='0.2.0', digest=None):
    name = f'AIClockIn-v{version}-windows-x64.exe'
    return {'tag_name': 'v' + version, 'body': '修复问题\n新增功能', 'draft': False, 'prerelease': False,
            'assets': [{'name': name, 'size': 4, 'digest': digest,
                        'browser_download_url': f'https://github.com/{u.REPO}/releases/download/v{version}/{name}'},
                       {'name': 'SHA256SUMS.txt', 'size': 200,
                        'browser_download_url': f'https://github.com/{u.REPO}/releases/download/v{version}/SHA256SUMS.txt'}]}


class Updates(unittest.TestCase):
    def test_network_retry_no_release_and_verified_ssl(self):
        error = URLError('offline')
        with patch.object(u, 'open_url', side_effect=error) as opened, patch.object(u.time, 'sleep'):
            with self.assertRaises(u.UpdateError):
                u.check('0.1.0')
            self.assertEqual(opened.call_count, 3)
        missing = HTTPError(u.API, 404, 'missing', {}, None)
        self.addCleanup(missing.close)
        with patch.object(u, 'open_url', side_effect=lambda url: (_ for _ in ()).throw(missing)
                          if url == u.API else io.BytesIO(b'{"private":false}')):
            with self.assertRaises(u.NoRelease):
                u.check('0.1.0')
        context = u.ssl.create_default_context()
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, u.ssl.CERT_REQUIRED)

    def test_primary_rate_limit_is_distinct_and_not_retried(self):
        error = HTTPError(u.API, 403, 'forbidden', {'X-RateLimit-Remaining': '0',
                         'X-RateLimit-Reset': '1794659800'}, io.BytesIO(b'{"message":"API rate limit exceeded"}'))
        with patch.object(u, 'open_url', side_effect=error) as opened:
            with self.assertRaisesRegex(u.RateLimited, '限流'):
                u.check('0.5.0')
        self.assertEqual(opened.call_count, 1)

    def test_permission_and_secondary_limit_are_distinct(self):
        for code, headers, body, expected in [
            (403, {}, b'{"message":"Forbidden"}', u.AccessDenied),
            (401, {}, b'{"message":"Bad credentials"}', u.AccessDenied),
            (403, {'Retry-After': '60'}, b'{"message":"secondary rate limit"}', u.RateLimited),
            (429, {}, b'not-json', u.RateLimited),
        ]:
            with self.subTest(code=code, headers=headers):
                error = HTTPError(u.API, code, 'test', headers, io.BytesIO(body))
                with patch.object(u, 'open_url', side_effect=error):
                    with self.assertRaises(expected):
                        u.check('0.5.0')

    def test_latest_404_does_not_hide_unavailable_repository(self):
        error = HTTPError(u.API, 404, 'missing', {}, io.BytesIO(b'{}'))
        with patch.object(u, 'open_url', side_effect=error):
            with self.assertRaisesRegex(u.UpdateError, '仓库') as caught:
                u.check('0.5.0')
        self.assertNotIsInstance(caught.exception, u.NoRelease)

    def test_cancel_and_truncated_download(self):
        item = u.parse_release(release(digest='sha256:' + 'a'*64), '0.1.0')
        with tempfile.TemporaryDirectory(dir=u.ROOT.parent) as folder:
            event = threading.Event(); event.set()
            for content, cancel in ((b'data', event), (b'x', None)):
                with patch.object(u, 'read_text', return_value='a'*64 + '  ' + item.name), \
                     patch.object(u, 'open_url', side_effect=lambda url: io.BytesIO(content)):
                    with self.assertRaises(u.UpdateError):
                        u.download(item, Path(folder), lambda *args: None, cancel)
                self.assertEqual(list(Path(folder).iterdir()), [])

    def test_numeric_version_and_release_filter(self):
        self.assertGreater(u.version('v0.1.10'), u.version('0.1.9'))
        for value in ('v1', '1.2.3-beta', '../1.2.3', '1.02.3'):
            with self.assertRaises(u.UpdateError):
                u.version(value)
        self.assertIsNone(u.parse_release(release(), '0.2.0'))
        self.assertIsNone(u.parse_release(release(), '0.3.0'))
        value = u.parse_release(release(), '0.1.0')
        self.assertEqual(value.notes, '修复问题\n新增功能')
        for key in ('draft', 'prerelease'):
            data = release(); data[key] = True
            with self.assertRaises(u.UpdateError):
                u.parse_release(data, '0.1.0')

    def test_asset_selection_and_https(self):
        for assets in ([], [release()['assets'][0]] * 2):
            data = release(); data['assets'] = assets
            with self.assertRaises(u.UpdateError):
                u.parse_release(data, '0.1.0')
        for url in ('http://github.com/a', 'https://evil.test/a', 'https://github.com@evil.test/a'):
            with self.assertRaises(u.UpdateError):
                u.safe_url(url)
        data = release(); data['assets'][0]['browser_download_url'] = 'https://github.com/evil/other/releases/download/v0.2.0/file.exe'
        with self.assertRaises(u.UpdateError):
            u.parse_release(data, '0.1.0')

    def test_checksums_missing_duplicate_conflict(self):
        name = release()['assets'][0]['name']; sha = 'a' * 64
        self.assertEqual(u.checksum(f'{sha}  {name}\n', name), sha)
        for body in ('', f'{sha}  other.exe', f'{sha}  {name}\n{sha}  {name}', f'zz  {name}'):
            with self.assertRaises(u.UpdateError):
                u.checksum(body, name)

    def test_download_integrity_progress_and_failure_preserves_target(self):
        content = b'MZxx'; digest = hashlib.sha256(content).hexdigest()
        item = u.parse_release(release(digest='sha256:' + digest), '0.1.0')
        with tempfile.TemporaryDirectory(dir=u.ROOT.parent) as folder:
            progress = []
            with patch.object(u, 'read_text', return_value=f'{digest}  {item.name}'), \
                 patch.object(u, 'open_url', side_effect=lambda url: io.BytesIO(content)), \
                 patch.object(u, 'validate_pe'):
                result = u.download(item, Path(folder), lambda n, total: progress.append((n, total)))
            self.assertEqual(result.read_bytes(), content)
            self.assertEqual(progress[-1], (4, 4))
            result.unlink()
            with patch.object(u, 'read_text', return_value=f'{digest}  {item.name}'), \
                 patch.object(u, 'open_url', side_effect=lambda url: io.BytesIO(b'evil')):
                with self.assertRaises(u.UpdateError):
                    u.download(item, Path(folder), lambda *args: None)
            self.assertFalse(result.exists())

    def test_checksum_digest_conflict_and_no_checksum_refused(self):
        data = release(digest='sha256:' + 'b'*64)
        item = u.parse_release(data, '0.1.0')
        with patch.object(u, 'read_text', return_value='a'*64 + '  ' + item.name):
            with self.assertRaises(u.UpdateError):
                u.expected_hash(item)
        data = release(); data['assets'] = data['assets'][:1]
        with self.assertRaises(u.UpdateError):
            u.expected_hash(u.parse_release(data, '0.1.0'))


if __name__ == '__main__':
    unittest.main()
