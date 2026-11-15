# 任务

| 编号 | 目标 | 状态 |
|---|---|---|
| TASK-001 | 独立核心签到桌面应用、后台自动、EXE 与本地 Git | 已交付；20 项测试及 EXE/Windows 验证通过，真实账号待验 |
| TASK-002 | GitHub 正式 Release 自动检查、下载校验、独立替换/恢复、发布规范 | v0.2.0 已实现并本地部署；43 项回归、隔离 EXE/任务/超时恢复通过；真实 GitHub Release 在线升级待发布后验证 |
| TASK-003 | 按用户授权提交 v0.2.0 并同步远程，编写明确提交说明 | 功能提交 a2f9f6d 已快进合入并推送 origin/main；未创建 GitHub Release |
| TASK-004 | README 下载文案通俗化，点击直接下载 EXE | 已改为程序文件直链；HTTP 200、二进制类型及文件大小核对通过 |
| TASK-005 | D 盘安装入口与当前用户桌面快捷方式，保留已有数据/任务 | v0.3.0 已本地部署并创建实际桌面图标；55 项回归及真实隔离验证通过；功能提交 18f0b0e，GitHub 网络失败，远程待同步 |
| TASK-006 | 优化设置样式、一键补建快捷方式，查明下载版启动提示 | v0.3.1 已部署并推送 main（0045103）；60 项回归、冻结 GUI 实际点击及 GitHub 下载哈希核对通过；可信签名未配置，SmartScreen 提示仍可能出现 |
| TASK-007 | 纠正文档对 Trae CN 多账号签到能力的误导 | 已区分账号管理与奖励领取，明确同设备多账号领取限制尚未解决；仅文档修改 |

| TASK-008 | PyInstaller 文件夹版 + Inno Setup 原生安装与完整目录更新 | v0.4.0 本地构建与隔离安装/升级/卸载、辅助更新通过；72 项回归通过；线上 Release 未发布，向导逐页交互未验证 |

| TASK-009 | 按授权提交 v0.4.0 源码/Setup 并更新 README 下载说明 | 已提交 1a4400b 并推送 origin/main；下载 HTTP 200、SHA256 一致；未创建正式 Release |

| TASK-010 | 重装后账号不可见及添加 Busy 排查 | 用户确认原账号和添加均恢复；v0.4.1 记住数据路径，卸载换目录重装回归通过，72项回归通过；未发布正式Release |

| TASK-011 | GitHub README 下载入口改为已验证的最新修正版 | v0.4.1 完整提交直链与版本说明已更新；远程结果见Git提交与交付报告 |

| TASK-012 | 本机源码目录丢失排查及恢复 | 已从远程8e8f30b恢复已提交源码，Git完整性通过；删除根因与未跟踪文件恢复待查 |

| TASK-013 | 排查异机安装自检失败，补充诊断、超时、安全恢复并重打包 | v0.4.2已打包并推送2f263c2，下载哈希一致；78项回归及原生诊断/旧版恢复/快捷方式/GUI通过；其他电脑复测未进行 |

| TASK-014 | 豆包工作真实只读数据来源最小验证，保留后续领取扩展边界 | 最小验证收尾：未通过接入门槛；用户未找到活动入口，页面级读取未执行；未新增空界面或修改现有功能 |


TASK-014 current recheck (2026-11-14): entry found and manual claim confirmed by user; actual app 2.36.15 and running process verified. Business read source remains unverified; UI connection unavailable. No implementation or package changes. Current evidence, changed files, validation limits and next steps: docs/DOUBAOWORK-RECHECK.md (DOUBAOWORK-RECHECK.md from docs/).


## TASK-015 (2026-11-14): Windows UIA read-only connection diagnosis

Completed connection diagnosis and real UI read verification, not provider integration. CUA host remains unavailable; native UIA Raw View reads real campaign and quota documents. Campaign cumulative=200; activity bonus used=0/200, remaining=200, repeated reads agree. Stable identity, explicit today-claimed state and actual daily receipt remain unverified. No core/database/task/package changes. Files: docs/DOUBAOWORK-UIA-DIAGNOSTICS.md, DOUBAOWORK-RECHECK.md, TASKS/HANDOFF/PROJECT/CHANGELOG; standalone probe/evidence under D workspace outputs. Validation commands, probe corrections, risk and next step are in the diagnostics report; no mock or real auto-claim tests, no build/commit/push. Next: verify account binding and explicit daily status before provider integration.


## TASK-016 (2026-11-14): DoubaoWork read-only quota implementation

Implemented Python/system-PowerShell UIA Raw View module and Tk quota panel; main account list includes an unbound read-only session. Each query records a distinct UUID in existing SQLite, preserving unknown values and encrypted accounts. No provider/scheduler/schema/installer/update changes; selfcheck assertion now includes the synthetic read-only row. Real campaign=200, real quota total=200/used=0/remaining=200 with expiry; minimized read passed and window restored. GUI/Store reopen verified using isolated data. Full unittest regression: 89 passed; final GUI-only: 1 passed; diff check passed. Lock screen, real scheduled tasks, closed client, slow page and other computers not live-verified; mocks are not real sign-in proof. No claim, package build, commit or push. Files, exact commands, screenshots, risks and next steps: docs/DOUBAOWORK-IMPLEMENTATION.md (DOUBAOWORK-IMPLEMENTATION.md from docs/). Next: stable account identity and explicit daily status, then separately validate packaging/background environments.


## TASK-017 (2026-11-14): DoubaoWork hardening and v0.5.0 installer

Built v0.5.0 onedir EXE and Inno Setup; desktop access guards and safe UIA error type/stage/codes added. Visible account handle is only a candidate, not verified stable identity; daily state remains unknown. 91 regression tests pass. Real normal/minimized quota reads, user-assisted lock-screen Win32 5 failure/NULL record, isolated native install/rollback/dependency diagnostics/shortcuts, actual scheduled EXE, local full-runtime helper update/restart/restore all verified. GitHub latest check HTTP403: online update unverified. Complete client exit test remains pending; other-PC compatibility unverified. No production data/task/core/schema/update logic changes, no upload/commit/push. Detailed files, commands, results, hashes, evidence and next steps: docs/DOUBAOWORK-RELEASE-VALIDATION.md (local docs: DOUBAOWORK-RELEASE-VALIDATION.md).

TASK-017 final addendum: real client exit was captured (multiple samples, independently zero DoubaoWork processes). Failure/NULL result persisted through the same record path in isolated SQLite; no false login/claim status. Probe stopped without restarting client. This supersedes the pending exit-test note above. Other-PC and online GitHub update remain unverified.


## TASK-018 (2026-11-14): v0.5.0 release readiness

Confirmed GitHub primary anonymous IP rate limit (60/0), classified limit/access/network/no-release/latest safely; after reset real latest404 + public repo200 yields NoRelease. No client token or proxy change. 95 regression tests pass; final candidate rebuilt with SHA256 2b8f6ab38b506acd584fcf73edc178ce5fbff7150de9238ef06bbb2a8317695a. Re-ran native install/rollback/dependency/shortcut checks, real scheduled EXE and helper update/restart/restore with both platform disabled synthetic accounts and history preserved. Cross-PC and online published-release full chain remain unverified. Sources/history/artifact audit and release notes/install checklist prepared. Development branch local commit only; no main merge, push, tag or GitHub Release. Full files, commands, limits and next steps: docs/RELEASE-0.5.0-READINESS.md (from docs: RELEASE-0.5.0-READINESS.md).


## TASK-019 (2026-11-14): authorized local merge into main

User requested merge and continuation. Initial worktree clean; no interrupted merge. Reviewed main...develop/v0.5.0-release-validation: diff check passed, original provider/auth/service/store/schedule/installer files unchanged. Local main fast-forwarded 906a920 -> 195ab57 without conflict using git merge --ff-only develop/v0.5.0-release-validation. Post-merge python -B -m unittest discover -s tests: 95 passed (11.627s). Development branch retained. No new application changes, rebuild or repeated installer tests needed because merged tree equals the tested candidate. Incremental records: docs/TASKS.md, docs/HANDOFF.md, CHANGELOG.md and docs/RELEASE-0.5.0-READINESS.md. No remote fetch/push, tag or Release publication; other-PC/online-release verification limits remain. Next: explicitly authorized remote synchronization or remaining release acceptance checks.


## TASK-020 (2026-11-14): authorized GitHub v0.5.0 publication

User explicitly requested publishing for local update testing. Pushed local main 31735cc after confirming remote had no newer commits; created reviewed draft, uploaded five assets and matched GitHub asset digests to local files, then published v0.5.0 as latest official release. Release URL: https://github.com/liangliang17655/AIClockIn/releases/tag/v0.5.0 . Tag resolves to 31735cc0eef8cf07a03912d24dbb1ba003907daf. Public update.check(0.4.2) detected v0.5.0 and remote notes; production download verified actual 13,869,293-byte Setup with SHA256 2b8f6ab38b506acd584fcf73edc178ce5fbff7150de9238ef06bbb2a8317695a; check(0.5.0) returned latest. No production installation was changed. Existing Git credential used in memory only; no token committed or embedded. README now links to Releases latest/download/AIClockInSetup.exe. Actual changed files: README, RELEASING, RELEASE-0.5.0-READINESS, TASKS/HANDOFF/PROJECT/CHANGELOG. Documentation diff check performed; no app changes or rebuild/repeated regression needed. Publication supersedes earlier no-release/HTTP403 observations; other-PC compatibility and user-machine end-to-end install still unverified. Next: user tests update from an older installed version; an already-installed 0.5.0 correctly reports latest. Evidence outside repo: D workspace outputs/AIClockIn-validation/release-0.5.0/published-release.json and public-download/verification.json.


## TASK-021 (2026-11-14): final goal is real DoubaoWork daily auto-check-in

User explicitly rejects read-only as final delivery. Rechecked official activity rules (HTTP200), public plugin API list, third-party recipe and existing UIA implementation. No confirmed platform-permitted claim channel; stable identity, current-day state and receipt evidence still missing. UIA quota/history and truthful locked/closed-client failure handling remain completed foundations, not auto-check-in. No claim or private API request, version/login recheck, business/database/task/update change, build, commit, push or publication. Actual files: AGENTS.md, README.md, docs/DOUBAOWORK-AUTOCHECKIN-GATE.md and PROJECT/TASKS/HANDOFF/CHANGELOG. Read-only document/source review and git diff --check; no sign-in test or mock claimed as real. Next: official permission/support channel, then minimum single-attempt idempotent flow and real post-claim verification subject to user confirmation. Full evidence, runtime conditions and gate: DOUBAOWORK-AUTOCHECKIN-GATE.md.


## TASK-022 (2026-11-14): targeted UIA sign-in spike

Added runnable tools/probe_doubao_signin.py and tests/verify_doubao_probe_task_windows.py, with docs/DOUBAOWORK-UIA-SPIKE.md. Real minimized UIA failure diagnosed; restoring existing window yields ~804 nodes, selects existing campaign tab and scrolls daily title. Banner 10 nodes (6Group/4Text), no Invoke/focusable/date/state. Actual InteractiveToken task ran three times with same observations, exit0, no claim, temporary task removed, production task unchanged. No reliable daily-state/button or pre/post receipt transition yet: need a real unclaimed versus manually claimed pair; cold activity-page navigation not verified. AST/diff checks and final direct smoke pass; no mock sign-in, no app/core/data/package changes, no commit/push. Previous dirty TASK-021 files retained. Next runnable sampling instructions and exact limits: DOUBAOWORK-UIA-SPIKE.md.


## TASK-023 (2026-11-14): real before/after observation preparation (in progress)

Added tools/doubao_compare.py (redacted campaign tree/text/banner capture and structural comparison), tools/schedule_doubao_before.py, tests/test_doubao_compare.py, docs/DOUBAOWORK-BEFORE-AFTER.md. Existing probe preserved. Real current-state capture: 238 nodes; public banner screenshot inspected, initial black/range errors diagnosed, no fake screenshot accepted. Real same-state comparison yielded zero differences and unknown state; not sign-in before/after evidence. Three comparison guard tests pass, pythonw actual capture exits0. Registered one-off InteractiveToken task AIClockIn-Doubao-Before-20261115 for 2026-11-15 00:05 +08, no late catchup/claim/restart; NextRunTime verified. Actual missing-tab test failed current normal navigation, user reopened activity page. Real unclaimed/claimed pair, reliable state/button/receipt recognizer remain pending next activity day and manual user claim. All prior dirty files retained; no app/core/data/installer/build/commit/push changes. Full commands, paths, failures, limitations and next step: DOUBAOWORK-BEFORE-AFTER.md. Need user message before manual claim to validate candidate or recapture; scheduled capture does not wake chat.


### TASK-023 progress: 2026-11-15 before-sample validation

Scheduled 00:05 capture ran exit0, 238 nodes/text/banner saved, but no new-day/status or sign button evidence. One normal UIA browser Refresh (no claim) followed by fresh capture at 00:11/00:13 revealed 239 nodes and one enabled Button named 立即签到 with Invoke. Original files retained; refreshed data stored as before-recheck-001/002.json under D workspace task023/20261115. Date in page still absent; pending user same-account/today confirmation and actual manual success/post sample. Passive bounded watcher started without restore/select/scroll/claim actions to capture user transition; not yet claimed success. Added passive and button-region capture options to comparison tool; identified blank PrintWindow button crop, rejected it as visual evidence and changed screenshot path to guarded foreground-only capture (post-change visual verification pending). Banner image reviewed as public promotional area, not sign status. Three comparison guard tests and syntax check pass; no core/database/package changes. User manual action requested asynchronously; no after sample or state recognizer yet. Before assessment: task023/20261115/before-assessment.json.


## TASK-024 (2026-11-15): user-authorized real single UIA check-in

Latest user explicitly requested automatic testing, superseding manual-only constraint for this single current-session experiment. Captured before; validated exactly one visible/enabled official Button with Invoke; created durable once-only ledger then invoked once at 00:23:55. Actual after snapshot at 00:23:56 contained official success toast, no sign button, cumulative200->400. Read-only official quota query00:25:20: total400/used0/remaining400. No retry, private API or credential/device changes. Current-day one-time test succeeded; daily integration and reliable persistent identity/state still not implemented. Released0.5.0 unchanged. Files: tools/doubao_compare.py passive/crop diagnostics, AGENTS, docs/DOUBAOWORK-AUTO-ONCE-RESULT.md and PROJECT/TASKS/HANDOFF/CHANGELOG. Three guard tests/AST/diff checks; no build/commit/push. Watcher stopped. Evidence under D workspace task023/20261115/auto-once-*.json. Next: integrate validated flow with identity, freshness, dedupe, navigation and truthful SQLite records, without repeating today claim.

## TASK-025 (2026-11-15): Doubao client preparation — partial
Added isolated startup/navigation worker and real scheduled validation. 107 unit tests passed; true cold launch once and warm/minimized menu navigation observed, but identity unknown and daily state unverified. No claiming, build or production task change. Files, commands, evidence and remaining gates: [session results](DOUBAOWORK-SESSION-RESULT.md).

## TASK-026 (2026-11-15): identity and daily-state evidence — partial
Visible Doubao number read twice in each of two real runs through official settings dialog; candidate only, no verified UID/binding/switch test. Historical239/251-node pair confirms one transient success, no business-date evidence. Added independent identity helper and sample auditor; 15 targeted tests pass. No claiming, production task/database change, build or publish. Files, commands, actual failures and next evidence: DOUBAOWORK-IDENTITY-STATE-RESULT.md.

## TASK-027 (2026-11-15): confirmed binding and dated official receipt — partial daily automation
Implemented user-confirmed DPAPI visible-number binding and before/after identity checks. User explicitly confirmed current source-account binding; real save/reload preserved old account/history hashes. Fixed settings-dialog close and active-tab return; official reward ledger now proves 2026-11-15 00:23 daily reward200. Real CLI, minimized client and temporary InteractiveToken task all reported already_signed, skipped claiming; live identity versus synthetic wrong binding stopped before navigation. Final133 unit tests pass. Unsigned state, real account switching and allowed claim chain remain unverified. Exact files, commands and evidence: DOUBAOWORK-BINDING-RESULT.md.

## TASK-028 (2026-11-15): unsigned candidate and delivery evidence — waiting for next day
Reuse original capture/UIA/scheduler; paired activity + official ledger bundle smoke passed on already-signed account, explicitly not unsigned proof. One-off 2026-11-16 00:05 +08 task registered and native NextRun/InteractiveToken/no-late-catchup verified. Pure delivery gate added with complete-before/after requirements, no submission code;142 tests pass. Future unsigned sample and new delivery real test pending. Scope/files/commands/evidence/terminal criterion: DOUBAOWORK-NEXT-DAY-RESULT.md.

## TASK-029 (2026-11-15): final delivery boundary and stop sampling
User explicitly stopped recurring research/sampling and accepts a working full implementation or a definite inability conclusion. Current implementation cannot deliver reliable Doubao unattended claiming: no proven dated unsigned/claimable state and no confirmed platform-permitted claiming route. No new scripts/features/build. Cancelled the verified one-off AIClockIn-Doubao-Before-20261116; production task unchanged. TASK-028 future sampling is cancelled, not pending automatic continuation. README/HANDOFF/CHANGELOG/PROJECT updated; only content/diff and native task removal checks needed.

## TASK-030 (2026-11-15): v0.5.1 stable local delivery
Hidden Doubao UI/research payload, preserved source and old records. Actual API403 remaining0 resolved through verified official stable Release fallback; public notes/download/SHA verified. Native helper caught cache/transaction-root incompatibility, fixed by preserving old transaction protocol and separating download cache; final rebuild passed.145 unit tests; real offline selftest/install/rollback/missing-dependency diagnostics/shortcuts/uninstall/helper restart/native task pass with synthetic disabled accounts. Final Setup13874856 bytes, SHA03378a93bf31c7819cfaf8a6c073ce4b67a5e904c9d13b8b222680aec1661351. Other-PC and real fresh claims untested; no GitHub publish. Files, commands, exact limits: STABLE-0.5.1-RESULT.md.
