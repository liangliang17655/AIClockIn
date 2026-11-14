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
