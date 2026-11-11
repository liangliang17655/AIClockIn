"""Limited MIT WorkBuddy local-login adapter.

Adapted from huxc573/AICreditPunch (v1.9.2 authentication portion).
Copyright (c) 2026 huxc573. MIT; see THIRD-PARTY-NOTICES.md.
Only local snapshot discovery and WorkBuddy's own decryption bridge are reused.
No check-in orchestration, account store, GUI or scheduled-task code is imported.
"""
from __future__ import annotations
import base64, binascii, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path
from typing import Any, Dict, List, Optional


def log(message):
    # Credential discovery never emits raw files or values into application logs.
    pass

def clean_text(value: Any) -> str:
    return str(value or "").strip()

WB_BASE_URL = "https://www.codebuddy.cn"

WB_AUTH_ENV = "WORKBUDDY_AUTH_FILE"

WB_AUTH_FILENAME = "workbuddy-desktop*.info"

WB_SNAPSHOT_GLOB = "*.info"

WB_PRODUCT_DIRS = ("CodeBuddyExtension", "WorkBuddy")

WB_AUTH_TAIL = ("Data", "Public", "auth")

WB_DADDY_DIR = "WorkDaddy"

WB_DADDY_ACCOUNTS = ("accounts", "profiles/*/accounts")

WB_DEFAULT_DOMAIN = "www.workbuddy.cn"

def _dedupe_paths(paths: Any) -> List[Path]:
    """按大小写不敏感的完整路径去重，保持原有顺序。"""
    unique: List[Path] = []
    seen = set()
    for path in paths:
        key = os.path.normcase(str(path))
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique

def wb_auth_dirs() -> List[Path]:
    """桌面端 auth 目录候选（Windows / macOS），有界、非递归、去重。"""
    home = Path.home()
    local = clean_text(os.environ.get("LOCALAPPDATA"))
    roots: List[Path] = [Path(local) if local else home / "AppData" / "Local"]
    roaming = clean_text(os.environ.get("APPDATA"))
    if roaming:
        roots.append(Path(roaming))
    suspects = [root.joinpath(product, *WB_AUTH_TAIL) for root in roots for product in WB_PRODUCT_DIRS]
    suspects += [home.joinpath("Library", "Application Support", product, *WB_AUTH_TAIL)
                 for product in WB_PRODUCT_DIRS]
    return _dedupe_paths(suspects)

def wb_daddy_auth_files() -> List[Path]:
    """WorkDaddy 的多账号快照：`<数据目录>/WorkDaddy/accounts/*.info`（`profiles/*/accounts/` 下是副本）。

    目录不存在就当没有，不报错 —— 没装 WorkDaddy 的用户走桌面端那一路，行为不变。
    """
    home = Path.home()
    local = clean_text(os.environ.get("LOCALAPPDATA"))
    roaming = clean_text(os.environ.get("APPDATA"))
    roots = ([Path(roaming)] if roaming else []) + [Path(local) if local else home / "AppData" / "Local"]
    files: List[Path] = []
    for root in roots:
        base = root / WB_DADDY_DIR
        if not base.is_dir():
            continue
        for pattern in WB_DADDY_ACCOUNTS:
            files.extend(sorted(base.glob(pattern + "/" + WB_SNAPSHOT_GLOB)))
    return _dedupe_paths(files)

class WbAuthSnapshot:
    """一个 `workbuddy-desktop*.info` 快照：解析出一条账号记录，绝不回显敏感值。"""

    def __init__(self, path: Path, quiet: bool = False) -> None:
        self.path = path
        self.record: Optional[Dict[str, Any]] = None
        self.expires_at: Optional[float] = None
        self.quiet = quiet
        self.skip_reason = ""

    @property
    def expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= time.time()

    def load(self) -> bool:
        """解析快照；不可用时打一行跳过原因并返回 False。"""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return self._skip("读取或 JSON 解析失败")
        auth = data.get("auth") if isinstance(data, dict) else None
        if not isinstance(auth, dict):
            return self._skip("缺少 auth 对象")
        token = self._plain(auth.get("accessToken") or auth.get("access_token"))
        cached = _WB_DECRYPTED.get(os.path.normcase(str(self.path))) or {}
        if not token:
            token = clean_text(cached.get("token"))
        if not token:
            if self._encrypted(auth.get("accessToken") or auth.get("access_token")):
                return self._skip("token 为加密格式且取密钥失败")
            return self._skip("缺少 accessToken")
        try:
            owner = self._pick_owner(data, token)
        except ValueError:
            return self._skip('账号主体与登录凭据不匹配')
        uid = clean_text(owner.get("uid") or owner.get("user_id")) or (_jwt_subject(token) or "")
        self.record = {
            "enabled": True,
            "name": self._display_name(owner, uid),
            "access_token": token,
            "uid": uid,
            "domain": clean_text(auth.get("domain") or owner.get("domain")) or WB_DEFAULT_DOMAIN,
            "enterprise_id": self._enterprise_id(owner, auth),
            "api_base": WB_BASE_URL,
        }
        if clean_text(cached.get("name")):
            self.record["name"] = clean_text(cached["name"])     # 昵称同批加密，用解密结果覆盖
        self.expires_at = self._expires_at(auth)
        return True

    def _skip(self, why: str) -> bool:
        self.skip_reason = why
        if self.quiet:
            return False                     # 自动同步：同类原因由 setup 汇总一行，不逐份刷屏
        log(f"跳过认证文件：{self.path}（{why}）")
        return False

    def _pick_owner(self, data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """挑出账号对象：先按 token 主体里的 uid 精确匹配，再退到「上次登录」标记。"""
        owners: List[Dict[str, Any]] = []
        for key in ("account", "accounts", "allAccounts"):
            value = data.get(key)
            if isinstance(value, dict):
                owners.append(value)
            elif isinstance(value, list):
                owners.extend(item for item in value if isinstance(item, dict))
        subject = _jwt_subject(token)
        if subject:
            matched = next((o for o in owners
                            if clean_text(o.get("uid") or o.get("user_id")) == subject), None)
            if matched:
                return matched
            if owners:
                raise ValueError('账号主体与登录凭据不匹配')
            return {'uid': subject}
        flagged = next((o for o in owners
                        if o.get("lastLogin") is True
                        or clean_text(o.get("lastLogin")).lower() in {"true", "1", "yes"}), None)
        return flagged or (owners[0] if owners else {})

    @staticmethod
    def _encrypted(value: Any) -> bool:
        """桌面端 / WorkDaddy 会把凭据字段换成本机密钥加密的 `{"$wbEncrypted":1,"envelope":…}`。"""
        return isinstance(value, dict) and ("envelope" in value or bool(value.get("$wbEncrypted")))

    @classmethod
    def _plain(cls, value: Any) -> str:
        return "" if cls._encrypted(value) else clean_text(value)

    def _display_name(self, owner: Dict[str, Any], uid: str) -> str:
        name = self._plain(owner.get("nickname") or owner.get("name") or owner.get("displayName")
                           or owner.get("username")) or clean_text(owner.get("uin"))
        if name:
            return name
        return f"账号-{uid[-8:]}" if uid else self.path.stem

    @staticmethod
    def _enterprise_id(owner: Dict[str, Any], auth: Dict[str, Any]) -> str:
        for source in (owner, auth):
            for key in ("enterpriseId", "enterprise_id", "tenantId", "tenant_id"):
                value = clean_text(source.get(key))
                if value:
                    return value
        return ""

    @staticmethod
    def _expires_at(auth: Dict[str, Any]) -> Optional[float]:
        """过期时间归一到秒；桌面端可能给毫秒时间戳。"""
        raw = auth.get("expiresAt") or auth.get("expires_at")
        if raw is None:
            return None
        try:
            value = float(str(raw))
        except (TypeError, ValueError):
            return None
        return value / 1000.0 if value > 100_000_000_000 else value

def _requested_auth_paths(explicit: Optional[str]) -> List[str]:
    """显式参数优先，其次环境变量（多个用系统路径分隔符）；都没有就返回空表示自动发现。"""
    if clean_text(explicit):
        return [clean_text(explicit)]
    from_env = clean_text(os.environ.get(WB_AUTH_ENV))
    if not from_env:
        return []
    return [item.strip() for item in from_env.split(os.pathsep) if item.strip()]

WB_EXE_ENV = "WORKBUDDY_EXE"

_WB_DECRYPTED: Dict[str, Dict[str, Any]] = {}

_WB_DECRYPT_JS = r"""
const fs = require('fs'), crypto = require('crypto');
let key = null;
try {
  const p = JSON.parse(process._linkedBinding('electron_browser_workbuddy_storage').loggerGet());
  key = crypto.createHash('sha256').update(p.atRestSecretKey, 'utf8').digest();
} catch (e) { key = null; }
const lp = s => { const b = Buffer.from(String(s), 'utf8'); const l = Buffer.alloc(4); l.writeUInt32BE(b.length); return Buffer.concat([l, b]); };
const u32 = n => { const b = Buffer.alloc(4); b.writeUInt32BE(n); return b; };
function open(v) {
  const e = JSON.parse(Buffer.from(v.envelope, 'base64').toString('utf8'));
  const aad = Buffer.concat([Buffer.from('WB-AAD\0', 'ascii'), Buffer.from([1]), lp('WBEV1'), lp('sym-v1'),
    u32(e.suite || 1), lp(e.keyId || ''), Buffer.from([2]), Buffer.from([0]), Buffer.from([0])]);
  const d = crypto.createDecipheriv('aes-256-gcm', key, Buffer.from(e.nonce, 'base64'), { authTagLength: 16 });
  d.setAAD(aad); d.setAuthTag(Buffer.from(e.authTag, 'base64'));
  return Buffer.concat([d.update(Buffer.from(e.ciphertext, 'base64')), d.final()]).toString('utf8');
}
const text = v => (v && typeof v === 'object' && v.envelope) ? open(v) : (typeof v === 'string' ? v : '');
const out = {};
if (!key) { process.stdout.write(JSON.stringify({ __error: 'no-key' })); process.exit(0); }
for (const f of process.argv.slice(2)) {
  try {
    const j = JSON.parse(fs.readFileSync(f, 'utf8').replace(/^\uFEFF/, ''));
    const a = j.auth || {};
    out[f] = { token: text(a.accessToken || a.access_token), name: text((j.account || {}).nickname) };
  } catch (e) { out[f] = { error: String(e.message || e).slice(0, 60) }; }
}
process.stdout.write(JSON.stringify(out));
"""

def _wb_registry_exe() -> List[str]:
    """Windows：从卸载项里找 WorkBuddy 主程序（有些机器不装在 %LOCALAPPDATA%\\Programs）。"""
    if not sys.platform.startswith("win"):
        return []
    try:
        import winreg
    except ImportError:
        return []
    found: List[str] = []
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for sub in (r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                    r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"):
            try:
                parent = winreg.OpenKey(root, sub)
            except OSError:
                continue
            for index in range(winreg.QueryInfoKey(parent)[0]):
                try:
                    key = winreg.OpenKey(parent, winreg.EnumKey(parent, index))
                    if "WorkBuddy" not in str(winreg.QueryValueEx(key, "DisplayName")[0]):
                        continue
                    icon = str(winreg.QueryValueEx(key, "DisplayIcon")[0]).split(",")[0].strip('"')
                    if icon:
                        found.append(icon)
                except OSError:
                    continue
    return found

def _wb_electron_exe() -> str:
    """能提供 atRestSecretKey 的 WorkBuddy 可执行文件；找不到返回空串。"""
    for name in (WB_EXE_ENV, "WORKDADDY_WB_EXE"):
        override = clean_text(os.environ.get(name))
        if override and Path(override).is_file():
            return override
    local = clean_text(os.environ.get("LOCALAPPDATA"))
    candidates: List[str] = []
    if local:
        for product, exe in (("WorkBuddy", "WorkBuddy.exe"), ("WorkBuddyAI", "WorkBuddyAI.exe")):
            candidates.append(str(Path(local) / "Programs" / product / exe))
    candidates.extend(_wb_registry_exe())
    if sys.platform == "darwin":
        candidates.extend(str(Path("/Applications") / app / "Contents" / "MacOS" / "Electron")
                          for app in ("WorkBuddy.app", "WorkBuddy AI.app"))
    candidates.extend(["/opt/WorkBuddy/workbuddy", "/opt/WorkBuddy/workbuddy-ai"])
    return next((item for item in candidates if item and Path(item).is_file()), "")

def _wb_decrypt_snapshots(paths: List[str]) -> None:
    """一次性解开全部加密快照，结果放 `_WB_DECRYPTED`（键为规范化路径）。"""
    if not paths:
        return
    exe = _wb_electron_exe()
    if not exe:
        log("加密快照未解密：未找到本机 WorkBuddy 程序（可用环境变量 WORKBUDDY_EXE 指定）")
        return
    workdir = Path(tempfile.mkdtemp(prefix="acp_wb_"))
    script = workdir / "open.js"
    data: Dict[str, Any] = {}
    try:
        script.write_text(_WB_DECRYPT_JS, encoding="utf-8")
        env = dict(os.environ, ELECTRON_RUN_AS_NODE="1")
        proc = subprocess.run([exe, str(script), *paths], env=env,
                              capture_output=True, timeout=60)
        text = proc.stdout.decode("utf-8", "replace").strip()
        start = text.find("{")
        if start >= 0:
            data = json.loads(text[start:]) if text.endswith("}") else json.loads(text[start:text.rfind("}") + 1])
    except (OSError, ValueError, subprocess.SubprocessError):
        data = {}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    if data.get("__error") == "no-key":
        log("加密快照未解密：本机 WorkBuddy 未提供密钥（未登录/版本不支持）")
        return
    for path, item in data.items():
        if isinstance(item, dict) and clean_text(item.get("token")):
            _WB_DECRYPTED[os.path.normcase(path)] = item
    if not _WB_DECRYPTED:
        log(f"加密快照未解密：{len(paths)} 份都没解开，本轮跳过")

def wb_auth_snapshots(explicit: Optional[str] = None, quiet: bool = False) -> List[WbAuthSnapshot]:
    """收集待解析的凭据快照（只列文件，不读内容）：桌面端当前登录 + WorkDaddy 各账号。"""
    requested = _requested_auth_paths(explicit)
    candidates: List[Path] = []
    if requested:
        for value in requested:
            path = Path(value).expanduser()
            if path.is_dir():
                candidates.extend(sorted(path.glob(WB_SNAPSHOT_GLOB)))
            elif path.is_file():
                candidates.append(path)
            else:
                log(f"未找到认证文件：{path}")
    else:
        for directory in wb_auth_dirs():
            if directory.is_dir():
                candidates.extend(sorted(directory.glob(WB_AUTH_FILENAME)))
        candidates.extend(wb_daddy_auth_files())      # WorkDaddy 多账号
    resolved: List[Path] = []
    for path in candidates:
        try:
            resolved.append(path.resolve())
        except OSError:
            resolved.append(path.absolute())
    snapshots = [WbAuthSnapshot(path, quiet=quiet) for path in _dedupe_paths(resolved)]
    encrypted: List[str] = []
    for snap in snapshots:
        try:
            data = json.loads(snap.path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        auth = data.get("auth") if isinstance(data, dict) else None
        value = auth.get("accessToken") or auth.get("access_token") if isinstance(auth, dict) else None
        if WbAuthSnapshot._encrypted(value):
            encrypted.append(str(snap.path))
    _wb_decrypt_snapshots(encrypted)          # 加密快照先统一解一遍，load() 直接取明文
    return snapshots

def _jwt_payload(token: str) -> Optional[Dict[str, Any]]:
    """解出 JWT 的 payload（不验签，只读 sub / exp）；解不了返回 None。"""
    parts = (token or "").split(".")
    if len(parts) != 3:
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)).decode("utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None

def _jwt_subject(token: str) -> Optional[str]:
    payload = _jwt_payload(token)
    return clean_text(payload.get("sub")) if payload else None

def _jwt_expires_at(token: str) -> Optional[float]:
    """JWT 里的 exp（秒）；读不到返回 None —— 用来判断两份凭据谁更新。"""
    payload = _jwt_payload(token) or {}
    raw = payload.get("exp")
    try:
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None
