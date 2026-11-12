"""Anonymous official Releases only; verified HTTPS and streaming SHA256 downloads."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import struct
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPSHandler, HTTPRedirectHandler, build_opener
import ssl

REPO = 'liangliang17655/AIClockIn'
API = f'https://api.github.com/repos/{REPO}/releases/latest'
ROOT = Path('D:/个人开发软件/AI工作区/temp/AIClockIn/updates')
MAX_PACKAGE = 160 * 1024 * 1024
HOSTS = {'api.github.com', 'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'}


class UpdateError(RuntimeError):
    pass


class NoRelease(UpdateError):
    pass


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r'v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', value):
        raise UpdateError('版本号格式无效，需要 v主版本.次版本.修订号')
    return tuple(map(int, value.lstrip('v').split('.')))


def safe_url(url):
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in HOSTS or parsed.username or parsed.password
            or parsed.port not in (None, 443) or parsed.fragment):
        raise UpdateError('更新地址不是允许的 GitHub HTTPS 地址')
    return url


class Redirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_url(url):
    safe_url(url)
    opener = build_opener(HTTPSHandler(context=ssl.create_default_context()), Redirects())
    return opener.open(Request(url, headers={'User-Agent': 'AIClockIn-updater', 'Accept': 'application/vnd.github+json'
                       if url == API else 'application/octet-stream'}), timeout=15)


def read_text(url, limit=2*1024*1024):
    for attempt in range(3):
        try:
            with open_url(url) as response:
                value = response.read(limit + 1)
            if len(value) > limit:
                raise UpdateError('更新信息超过大小限制')
            return value.decode('utf-8-sig')
        except HTTPError as exc:
            if exc.code == 404 and url == API:
                raise NoRelease('尚未发布正式版本，请稍后再检查') from None
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise UpdateError(f'GitHub 请求失败（HTTP {exc.code}），请稍后重试') from None
        except (OSError, URLError, UnicodeError, TimeoutError):
            if attempt == 2:
                raise UpdateError('连接 GitHub 失败，请检查网络后重新检查') from None
        time.sleep(0.5 * (attempt + 1))


@dataclass(frozen=True)
class Release:
    tag: str
    notes: str
    name: str
    url: str
    size: int
    checksum_url: str | None
    digest: str | None
    kind: str = 'portable'


def parse_release(data, local):
    if not isinstance(data, dict) or data.get('draft') is not False or data.get('prerelease') is not False:
        raise UpdateError('只接受正式发行版本')
    tag = data.get('tag_name')
    remote = version(tag)
    if remote <= version(local):
        return None
    normalized = '.'.join(map(str, remote))
    setup_name = f'AIClockIn-v{normalized}-Setup-windows-x64.exe'
    available = data.get('assets', [])
    setup = isinstance(available, list) and any(isinstance(a,dict) and a.get('name')==setup_name for a in available)
    name = setup_name if setup else f'AIClockIn-v{normalized}-windows-x64.exe'
    assets = data.get('assets', [])
    if not isinstance(assets, list):
        raise UpdateError('Release 附件格式无效')
    def asset(filename, required):
        matches = [a for a in assets if isinstance(a, dict) and a.get('name') == filename]
        if len(matches) > 1 or (required and not matches):
            raise UpdateError(f'Release 缺少唯一附件：{filename}')
        if not matches:
            return None
        a = matches[0]
        url = safe_url(a.get('browser_download_url', ''))
        if not url.startswith(f'https://github.com/{REPO}/releases/download/{tag}/') or urlsplit(url).path.rsplit('/', 1)[-1] != filename:
            raise UpdateError('Release 附件不属于指定仓库、标签或文件名')
        return a
    exe, sums = asset(name, True), asset('SHA256SUMS.txt', False)
    size = exe.get('size')
    if not isinstance(size, int) or isinstance(size, bool) or not 0 < size <= MAX_PACKAGE:
        raise UpdateError('安装包大小无效')
    digest = exe.get('digest')
    if digest is not None and not re.fullmatch('sha256:[0-9a-fA-F]{64}', digest):
        raise UpdateError('Release SHA256 digest 无效')
    notes = data.get('body') or '发布者没有填写更新说明。'
    if not isinstance(notes, str):
        raise UpdateError('更新说明格式无效')
    return Release(tag, notes, name, exe['browser_download_url'], size,
                   sums['browser_download_url'] if sums else None, digest[7:].lower() if digest else None,
                   'setup' if setup else 'portable')


def check(local):
    try:
        return parse_release(json.loads(read_text(API)), local)
    except (ValueError, TypeError, KeyError):
        raise UpdateError('GitHub 返回的更新信息无效') from None


def checksum(text, name):
    matches = []
    for line in text.splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]{64})[ \t]+\*?([^\r\n]+)', line)
        if match and match[2] == name:
            matches.append(match[1].lower())
    if len(matches) != 1:
        raise UpdateError('SHA256 校验文件缺少唯一且有效的安装包记录')
    return matches[0]


def expected_hash(item):
    value = checksum(read_text(item.checksum_url, 64*1024), item.name) if item.checksum_url else item.digest
    if not value or (item.digest and value != item.digest):
        raise UpdateError('缺少可信 SHA256，或校验文件与 Release digest 不一致')
    return value


def file_hash(path):
    sha = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(256*1024), b''):
            sha.update(block)
    return sha.hexdigest()


def validate_pe(path):
    with Path(path).open('rb') as stream:
        if stream.read(2) != b'MZ':
            raise UpdateError('安装包不是 Windows EXE')
        stream.seek(0x3c)
        data = stream.read(4)
        if len(data) != 4:
            raise UpdateError('EXE 文件头损坏')
        offset = struct.unpack('<I', data)[0]
        if offset > 1024*1024:
            raise UpdateError('EXE 文件头位置无效')
        stream.seek(offset)
        if stream.read(6) != b'PE\0\0\x64\x86':
            raise UpdateError('只支持 Windows x64 安装包')


def download(item, folder, progress, cancel=None):
    cancel = cancel or threading.Event()
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    digest = expected_hash(item)
    part, target = folder / (item.name + '.part'), folder / item.name
    deadline = time.monotonic() + 600
    for attempt in range(3):
        try:
            count = 0
            with open_url(item.url) as response, part.open('wb') as stream:
                while True:
                    if cancel.is_set():
                        raise UpdateError('下载已取消，当前版本未修改')
                    if time.monotonic() > deadline:
                        raise UpdateError('下载超时，请重试')
                    block = response.read(128*1024)
                    if not block:
                        break
                    count += len(block)
                    if count > item.size:
                        raise UpdateError('下载大小超过 Release 声明')
                    stream.write(block)
                    progress(count, item.size)
            if count != item.size or file_hash(part) != digest:
                raise UpdateError('安装包大小或 SHA256 校验失败，当前版本未修改')
            validate_pe(part)
            part.replace(target)
            return target
        except (OSError, URLError, TimeoutError):
            if attempt == 2:
                raise UpdateError('安装包下载失败，请检查网络后重试') from None
            cancel.wait(0.5 * (attempt + 1))
        finally:
            part.unlink(missing_ok=True)
    raise UpdateError('下载失败')
