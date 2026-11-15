import io
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from aiclockin import update as u


class Response(io.BytesIO):
    def __init__(self, content=b'',url='',headers=None):
        super().__init__(content);self.url=url;self.headers=headers or {}
    def geturl(self):return self.url


class FallbackTests(unittest.TestCase):
    def opener(self, url):
        if url==u.API:
            raise HTTPError(url,403,'limit',{'X-RateLimit-Remaining':'0'},io.BytesIO(b'{}'))
        tag=f'https://github.com/{u.REPO}/releases/tag/v0.5.1'
        if url.endswith('/releases/latest'):return Response(url=tag)
        if url.endswith('/releases.atom'):
            return Response((f'<feed xmlns="http://www.w3.org/2005/Atom"><entry><link rel="alternate" href="{tag}"/>'
                '<content type="html">&lt;p&gt;Repair&lt;/p&gt;</content></entry></feed>').encode())
        if url.endswith('SHA256SUMS.txt'):return Response(('a'*64+'  AIClockIn-v0.5.1-Setup-windows-x64.exe').encode())
        return Response(headers={'Content-Length':'1234'})

    def test_limited_api_uses_official_release_and_verified_checksum(self):
        with patch.object(u,'open_url',side_effect=self.opener):
            result=u.check('0.5.0')
        self.assertEqual(result.tag,'v0.5.1');self.assertEqual(result.kind,'setup')
        self.assertEqual(result.digest,'a'*64);self.assertEqual(result.size,1234)
        self.assertIn('Repair',result.notes)

    def test_latest_comparison_needs_no_asset_download(self):
        with patch.object(u,'open_url',side_effect=self.opener) as opened:
            self.assertIsNone(u.check('0.5.1'))
        self.assertEqual(opened.call_count,2)

    def test_wrong_repository_or_prerelease_redirect_is_refused(self):
        for target in ('https://github.com/evil/other/releases/tag/v0.5.1',
                       f'https://github.com/{u.REPO}/releases/tag/v0.5.1-beta'):
            def bad(url):
                if url.endswith('/releases/latest') and url!=u.API:return Response(url=target)
                return self.opener(url)
            with patch.object(u,'open_url',side_effect=bad):
                with self.assertRaises(u.RateLimited):u.check('0.5.0')
