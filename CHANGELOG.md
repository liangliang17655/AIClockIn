# 变更记录

## 能力说明修正 · TASK-007 · 2026-11-11

- 删除 README 中不加限定的“WorkBuddy 和 Trae CN 多账号签到”宣传，明确 Trae CN 同设备多账号领取限制尚未解决；保存多个账号不代表全部可领取，9095 仍为设备受限。
- 同步项目能力边界、任务与交接。仅修改文档，不修改签到代码或 EXE、不重新打包；检查文案及 git diff --check。

## 0.3.1 · TASK-006 · 2026-11-11

- 后续同步已完成：沿用当前 Windows 系统代理临时路由推送 main，功能提交 0045103；GitHub 直链重新下载的 EXE 哈希与本机 0.3.1 一致，未改持久代理设置或创建正式 Release。

- 设置改为与主界面一致的白底下拉面板、蓝色开关及统一操作行，支持键盘、Esc 和点击外部收起。
- 设置中创建桌面快捷方式改为后台直接完成，取消二次安装窗口，明确成功/失败提示且不清除原签到忙碌状态。
- 重新下载 GitHub 0.3.0 核对哈希并实际启动；用户截图确认 Windows SmartScreen 未知发布者提示，README 补首次运行说明。0.3.1 仍未可信签名，不宣称安全提示消失，不更改系统防护。
- 60 项回归及真实冻结界面菜单点击、快捷方式成功/冲突反馈通过；原数据文件哈希和任务 XML 保持不变。完整证据及未验证项见 docs/SETTINGS-FIX.md、docs/HANDOFF.md。

## 0.3.0 · TASK-005 · 2026-11-11

- 同一单文件 EXE 增加首次安装窗口，新用户默认 D:/AIClockIn，自动创建当前用户桌面的“AIClockIn 自动签到”；设置菜单可补建入口。
- 识别来源目录、原自动任务及默认目录已有账号，保留 EXE/data/任务绝对路径，不迁移账号；后台和自检不进入安装。
- 安装先校验/健康检查，覆盖旧程序复用更新事务；快捷方式保留显式 --data，原子创建且拒绝覆盖不同目标，错误可重试。
- 55 项回归通过，真实隔离首启路由/安装/.lnk 启动/重复安装/旧版原地升级/任务触发与清理通过；本机已部署 0.3.0，实际账号等文件哈希和任务 XML 未变，桌面图标已创建。
- 修改文件、实际命令、审查修复和未验证项见 docs/INSTALL-PLAN.md、docs/HANDOFF.md；未发布 GitHub Release。

## 直接下载入口 · TASK-004 · 2026-11-11

- README 将入口改为“点击下载自动签到软件（Windows 电脑版）”，直接下载仓库中已有的 AIClockIn.exe，简化首次使用步骤。
- HEAD 核对直链返回 HTTP 200、二进制类型和正确文件大小；同步任务/交接记录。仅文档改动，无应用代码、自动更新来源或 EXE 变化。

## 远程交付 · TASK-003 · 2026-11-11

- 用户明确授权提交推送；将 v0.2.0 功能提交 a2f9f6d 快进合入 main 并成功推送 origin/main，提交正文包含功能、数据保护、验证结果及未验证项。
- 提交前重新运行 43 项测试全部通过，暂存差异检查通过，账号和 data 未上传；同步任务及交接记录，无应用逻辑变更。
- 此次仅提交代码和现有跟踪产物，未创建正式 GitHub Release；下载安装入口及真实在线升级仍需正式发布附件。

## 0.2.0 · TASK-002 · 2026-11-11

- 核实当前为 v0.1.0 便携单文件版、实际数据路径及现有计划任务；GitHub 当前无正式 Release。
- 新增 docs/UPDATE-DESIGN.md，明确异步检查、Release 附件与 SHA256、独立辅助替换、数据保护、恢复机制、发布规范及 12 项验收安排；同步任务和交接。
- 用户确认后实现右上角设置、异步正式 Release 检查、远程说明、下载进度/取消、HTTPS 和 SHA256 校验、独立本地辅助替换、健康检查/恢复和重启。
- 新增 Windows Job 进程树隔离及备份/暂存强制落盘；中断恢复与失败反馈，保持原 EXE 绝对路径与 data/任务不变，不改签到核心。
- 新增本地发布脚本、版本化 EXE/SHA256SUMS 及发布文档，README 添加直接下载入口；不提交、推送或发布 Release。
- 43 项回归通过；真实隔离 EXE 替换/重启/任务/合成 DPAPI 数据保留及冻结自检超时恢复通过。原位置部署 v0.2.0，实际数据文件哈希与任务 XML 未变。
- 正式 GitHub Release 在线升级、实体断电及真实账号签到尚未验证。完整文件、命令、审查结果和边界见 docs/UPDATE-VALIDATION.md、docs/HANDOFF.md。

## 0.1.0 · TASK-001 · 2026-11-11

- 根据用户确认，在空目录创建独立本地 Git 仓库和开发记录，建立敏感数据忽略规则。
- 尚未提交或推送，旧项目文件、账号与任务未修改。
- 新增本项目独立的结构化结果、HTTP、平台执行、账号加密、历史、服务、后台任务与全新 Tkinter 页面；仅有限复用署名的本机 WorkBuddy 登录适配，没有整体搬入旧脚本。
- 保留两个平台、多账号顺序执行、查询、简单记录与后台自动；没有快照按钮、推送、设备模拟或复杂报表。
- 修复开发审查发现的账号主体错绑和后台数据路径丢失；拒绝未知状态领取，9095 如实记设备受限。
- 20 项测试通过，默认/小窗口截图已检查，单文件 EXE 离线自检及真实 Windows 临时任务执行/清理通过。实际文件、命令、风险和未验证项见 docs/HANDOFF.md。
- 真实账号尚未在新项目验证；默认不迁移旧数据或注册生产任务。初次添加后需点“开启自动签到”。


## 0.4.0 · 2026-11-12 · TASK-008

改用 PyInstaller 文件夹 + Inno Setup 原生向导、桌面/开始菜单和卸载登记；更新辅助程序处理完整依赖、校验、失败恢复和自动重启。账号/历史/任务路径不变；修复更新弹窗关闭错误。72项回归、真实隔离安装/升级/卸载/辅助更新通过；线上 Release 未发布。详情见 docs/INNO-PLAN.md。


## TASK-009 · 2026-11-12 · 提交 v0.4.0 与更新下载说明

用户明确授权提交并推送远程。更新 README 的原生安装包直链、安装及旧版迁移说明；补充 .gitignore 排除本地安装依赖和卸载元数据。发布已验证的根 AIClockInSetup.exe，不提交本地已安装的 AIClockIn.exe 改动、data 或运行目录。TASK-008 的源码、测试及文档一起交付。远程核对 origin/main 基线仍为 9843ae8，无新增远程提交。

验证沿用 TASK-008 最新72项回归及原生安装/更新测试（业务代码未再改动）；本次执行 git diff --check、暂存清单检查、安装包 SHA256、远程提交核对与直链下载校验。未创建正式 Release；软件内线上更新仍待正式发布后验证。提交/推送结果以 Git 历史和最终交付报告为准。


## TASK-010 · 2026-11-12 · 本机故障恢复

修复本机新安装读取空数据目录的配置，原3个账号仍在且未修改；未修改源码/安装包、未提交推送。添加 Busy 尚未复现，不能标记已修复；验证和回退路径见 HANDOFF。


### TASK-010 最终修复与验证

用户确认“账号恢复了，添加也正常”。没有证据表明持久锁残留，未删除锁/改写并发控制；不能保证真实操作并发时永不出现 Busy。

针对再次卸载重装：真实隔离测试先在旧脚本复现“Reinstall forgot retained account directory”，再修改 installer/AIClockIn.iss：健康检查通过后保存当前用户数据路径到独立 HKCU Software/AppId；卸载保留此值；重装仅复用仍有账号或历史文件的 D 盘目录，显式 /DATA 优先。不复制/覆盖用户数据、不扫描全盘。当前用户已验证旧路径也已登记，本机匹配目标的桌面/开始菜单入口指向原数据。

版本0.4.1；修改 VERSION、installer/AIClockIn.iss、tests/verify_inno_windows.py、tests/test_installer.py、README、RELEASING、TASKS、HANDOFF、CHANGELOG及根Setup。旧单元测试假设 D:/AIClockIn 尚未安装，在本机安装后失败；将其默认目录改为独立临时夹，未改变产品行为。

命令与结果：python -B tests/verify_inno_windows.py --reuse-bundle 新增卸载换目录重装读取原账号/历史与数据哈希不变通过，已有安装/升级/失败恢复/任务/卸载清理继续通过；python -B -m unittest discover -s tests -q：72项通过。release.ps1 -Bundle dist/test-bundle/v0.4.1/AIClockIn：exit0，自检版本0.4.1与编译通过。复用先前验证过的同源码0.4.1完整目录，不重复构建未变化Python核心。

Setup SHA256：63616502fc03b367b0bd98583be326a529c37602c3aa558d9391c90945e10016。未执行真实签到。未发布GitHub正式Release，未重新运行未改变的完整更新辅助链路；当前运行应用代码不变，仅安装器修复。用户手动删除原data、换Windows用户/机器不保证恢复。后续以提交记录确认远程分发；不将本机配置、账号或登记数据上传。


## TASK-011 · 2026-11-12 · 修正远程 README 下载入口

用户要求 GitHub 页面下载入口也为最新版。根安装包已在9872aaa上传，但 main 原始文件地址曾返回旧0.4.0缓存。将 README 下载链接改为完整提交9872aaaabfe020991867c40ff80d90785cf2e589对应的0.4.1 Setup，注明当前版本；RELEASING要求后续每次上传安装包后更新README已验证提交地址。只修改 README、RELEASING、TASKS、CHANGELOG、HANDOFF，不改程序或用户数据。

验证：该固定地址先前实际 HTTP200，13,848,240字节，SHA256 63616502fc03b367b0bd98583be326a529c37602c3aa558d9391c90945e10016，与本地修正版一致；本次检查文案与 git diff --check，并在推送后核对远程README。文档修改不重复构建/运行程序测试。未创建正式Release；未来新版仍须按发布步骤同步README，不声称固定提交URL会自动变化。


## TASK-012 · 2026-11-12 · 源码目录丢失恢复

用户反馈源码被删除。检查时项目目录仅余 .git/objects，git status/log均报非仓库，确认本机源码确实缺失；不根据缺失现象推断删除者或原因。现有安装脚本无 UninstallDelete/DelTree/源码目录递归清除规则，未找到能证明此次删除来源的证据，等待用户说明此前安装/卸载操作。

恢复：从公开远程克隆到 D:/个人开发软件/AI工作区/temp/AIClockIn-source-recovery-20261112，核对残留文件冲突后，仅复制缺失文件回原目录，未覆盖残留文件，未 reset/clean/递归删除。恢复101个缺失文件（含Git元数据）；远程最新提交8e8f30b。当前D:/AIClockIn数据不改写；未提交源码和原本地data不属于Git可恢复内容，未声称已恢复。

验证：恢复后 git status --short无输出，git log -1=8e8f30b；git fsck --connectivity-only通过，git ls-files --deleted无输出；main.py/README/AGENTS/aiclockin/gui.py存在。未改业务代码，不重复构建或运行全量测试。此次仅增量更新TASKS/HANDOFF/CHANGELOG以记录恢复事实，未提交/推送。风险：删除根因未确定、原未跟踪文件可恢复性未知；下一步核对用户最近的安装/卸载目录，避免源码与运行安装目录混用。


## TASK-013 · 2026-11-14 · 安装自检跨电脑失败诊断修复

根因证据、影响范围、完整修改清单与测试边界见docs/INSTALL-DIAGNOSTICS.md。已确认旧安装器{tmp}报告在C时被main的D盘约束拒绝，且异常被通用提示掩盖；首次失败留下启动文件也已复现并修正。版本0.4.2保留自检/版本/失败恢复，增加D盘阶段诊断、90秒原生进程等待与句柄关闭，安装版.runtime不再依赖开发机目录；selfcheck禁用网络和任务探测。签到核心和生产账号/任务不改。

实际文件：.gitignore、VERSION、main.py、aiclockin/selfcheck.py、runtime.py、gui.py、installer/AIClockIn.iss、tests/test_selfcheck.py、verify_install_diagnostics_windows.py、docs/INSTALL-DIAGNOSTICS.md、TASKS/HANDOFF/CHANGELOG、根Setup及后续README下载说明。保留原TASK-012未提交恢复记录。

验证：78项unittest通过；build与release exit0；真实原生超时/版本不符恢复旧4.1哈希、合成账号/SQLite/历史、任务XML保持；故意缺_tkinter依赖输出类型/阶段/堆栈且首次失败EXE清理；首装桌面/开始菜单、正常GUI/.runtime及卸载自有链接通过。独立审查发现终止状态检查问题已修复，原生进程实现复核通过。其他实体电脑、Defender隔离、真实C-TEMP启动原生Setup均未实测。未关闭防护，未发布正式Release。下一步由对方复测并提供诊断文件，远程分发结果以最终提交记录为准。


## TASK-014 · 2026-11-14 · 豆包工作最小可行性验证

用户批准分阶段推进，最终目标包含自动签到、额度及记录；本轮自动领取不实施。实际核查官方应用插件登录/API范围、Android SAEP适用边界及本机签名客户端只读可访问性。用户确认已登录后，UIA主窗仅4个后代、全部目标窗口复查为4/14个后代，均未取得账号/签到/余额文本；MSAA根入口可用但未取得业务数据。活动/额度页身份尚待用户确认，不声称所有页面已验证失败。官方公开文档范围也未找到个人奖励查询渠道。

结论：未通过实施门槛，暂不增加GUI/账号项/空平台实现。后续query/claim能力隔离契约与去重要求已写入docs/DOUBAOWORK-FEASIBILITY.md，长期目标保留。实际修改仅该验证文档、PROJECT/TASKS/HANDOFF/CHANGELOG。未读凭据、未设置调试端口、未发领取请求、未改现有核心/数据/任务/安装包、未提交推送。

验证命令/结果：git status接入干净；Get-CimInstance/Get-Process及文件签名元数据只读检查通过；System.Windows.Automation定向探测返回外壳控件，无可用业务字段；AccessibleObjectFromWindow返回0仅根层可用。详细探针边界及一次.NET属性探针错误均如实记在可行性文档。证据在D工作区outputs/AIClockIn-validation/doubaowork，未记录账号秘密。业务代码未变，未运行全量测试/构建。风险：UI数据和平台许可均未核实；下一步继续已登录官方活动页验证，失败则按文档给出的官方支持/可访问性路线，不伪造查询完成。


TASK-014 收尾补充：用户回复“找不到活动入口”。本轮未通过接入门槛，活动页实际读取未执行，不把该事实解释为登录失效/已签到/无活动资格。当前不再等待页面打开；未来取得官方接口/授权或可访问性支持、定位实际入口后重新验证。仅更新验证文档与任务/交接记录，原软件及安装包不变；未提交推送。


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
