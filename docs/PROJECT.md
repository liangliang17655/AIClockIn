# AIClockIn

## 需求与验收（用户已确认）

2026-11-11，独立新项目。用户希望只保留核心签到功能，全新页面，本地 Git 仓库，日后自行上传 GitHub；保留后台自动签到。

- 支持 WorkBuddy / Trae CN 多账号添加、重命名、启停、删除。
- 实际边界：上述多账号是凭据保存和管理能力，不代表 Trae CN 同设备的多个账号均能领取。Trae CN 设备领取限制尚未解决，9095 如实记录为设备受限；对外文档不能将其宣传为同设备多账号全部签到成功。
- 一个“立即签到”依次执行所有启用账号；一个失败继续下一个，已签不重复领，领取后回查。
- 展示简单持久记录：时间、账号、结果、当次获得、余额、失败原因。未知值不填 0。
- 主界面明确自动签到是否启用，关闭窗口不影响后台任务；Windows 当前用户登录状态下独立运行 EXE --silent。
- 不保留推送、手动快照入口、设备模拟、旧命令集合及复杂报表。
- 账号在本项目 data 内加密保存，不读写旧软件账户；更新保留 data。不能保证平台不允许的账号均能领取。

## 架构

- aiclockin/models.py：结构化签到结果。
- aiclockin/http.py、providers.py：本项目独立 HTTP 和两个平台核心流程，接口事实参照已验证实现，不导入旧项目模块。
- aiclockin/auth.py：Trae 浏览器授权、本机登录读取；workbuddy_auth.py 仅承载署名的 MIT 本机登录适配。
- aiclockin/store.py：DPAPI 账号、SQLite 历史、跨进程互斥。
- aiclockin/service.py：逐账号执行、凭据更新、脱敏后的记录。
- aiclockin/schedule.py：一个独立 AIClockIn-Auto 任务，包含每日、登录及恢复触发。
- aiclockin/gui.py：全新简洁窗口；独立 worker 处理网络，界面只读结果。
- main.py：GUI / --silent / 账号授权 / 自动设置 / 离线自检入口。
- build.ps1：D 盘隔离构建并打包单文件 EXE。

## 决策

- TASK-006：仅优化设置菜单，保持现有主界面布局和浅色配色；SettingsMenu 管理弹层，UpdateUI 使用事件队列回传快捷方式结果，不再为补入口拉起安装器。用户下载版的蓝色提示已确认是 SmartScreen；没有可信证书，不自动解除下载标记、关闭防护或伪造发布者，不将 GUI 修复等同于数字签名。

- TASK-005，2026-11-11 用户确认：增加安装入口和桌面快捷方式。复用同一单文件的 installer.py，不引入安装框架；新用户默认 D:/AIClockIn，已有用户保留当前 EXE/data/任务路径，不迁移账号。桌面 .lnk 按 Windows 当前用户实际桌面位置写入（用户明确授权桌面入口，可能在 C 盘，仅写快捷方式）。详见 [安装方案与验证](INSTALL-PLAN.md)。
- 首次无本地数据且无显式 --data 的冻结 GUI 显示安装窗口，在创建 Store 前完成路由；后台任务、自检和更新辅助不进入安装。设置菜单支持为原目录补快捷方式。链接目标和 --data 使用绝对路径；不同目标同名链接拒绝覆盖。

- TASK-002，2026-11-11 用户确认：增加 GitHub 正式 Release 自动更新，继续便携单文件形式，使用本地 EXE 副本作为独立辅助程序，仅替换原绝对路径的 EXE；不迁移 data，不重建计划任务。详见 [技术方案](UPDATE-DESIGN.md)、[发布说明](RELEASING.md) 和 [验证记录](UPDATE-VALIDATION.md)。
- 更新模块：update.py 负责 Release/HTTPS/校验；update_gui.py 负责菜单和异步交互；update_apply.py 负责互斥、替换、恢复和重启；health_process.py 用 Windows Job 隔离新版自检进程树；version.py 读取包内 VERSION。main.py 在访问真实数据前协调更新。检查只在 GUI 启动，不在静默签到和健康检查中运行。

- 已批准：Python + Tkinter，保留后台定时功能。
- 实现选择：单个 Windows 任务减少管理复杂度；固定每日六次并补登录/恢复，界面不提供复杂定时表达式。
- 实现选择：默认不注册系统任务，首次界面清楚显示“未开启”；由用户显式点击开启，不干扰旧软件。
- 实现选择：独立数据、独立任务；旧账户与任务不自动迁移。
- 实现选择：应用自主编写；有限 MIT 登录适配如实保留来源和许可，不声称严格 clean-room。
- 授权仅限正常平台流程；Trae 实际设备标识取本机客户端，不生成领取用的替代设备身份。

未验证：真实接口在新项目中的当前可用性、用户是否需要后续迁移旧账号。未做任何数据迁移。


## TASK-008 · 已确认的分发架构变更（2026-11-12）

用户明确指定并批准 PyInstaller --onedir → Inno Setup 原生安装包，替代此前单文件/自制安装入口的选择。程序依赖目录按版本与构建标识隔离，完整目录辅助更新，同路径安装保护计划任务；data 不打包、不覆盖。Setup 当前用户运行，避免 DPAPI 身份变化；支持桌面、开始菜单、卸载。旧版首次需手动 Setup；并非已发布线上版本。实际结果及边界见 INNO-PLAN.md。


## TASK-014 · 豆包工作分阶段目标（2026-11-14，用户已确认）

最终目标为豆包工作自动签到、额度查询与持久记录。本轮先验证真实且符合规则的只读渠道，验证通过后才接入现有账号/GUI/SQLite；自动领取暂不实施，后续须有平台允许方案并另行确认。本机初步可访问性探测未取得业务字段，实施门槛未通过，不新增仅打开网页的占位平台。详情和实际边界见 [最小验证记录](DOUBAOWORK-FEASIBILITY.md)。


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


## TASK-020 (2026-11-14): authorized GitHub v0.5.0 publication

User explicitly requested publishing for local update testing. Pushed local main 31735cc after confirming remote had no newer commits; created reviewed draft, uploaded five assets and matched GitHub asset digests to local files, then published v0.5.0 as latest official release. Release URL: https://github.com/liangliang17655/AIClockIn/releases/tag/v0.5.0 . Tag resolves to 31735cc0eef8cf07a03912d24dbb1ba003907daf. Public update.check(0.4.2) detected v0.5.0 and remote notes; production download verified actual 13,869,293-byte Setup with SHA256 2b8f6ab38b506acd584fcf73edc178ce5fbff7150de9238ef06bbb2a8317695a; check(0.5.0) returned latest. No production installation was changed. Existing Git credential used in memory only; no token committed or embedded. README now links to Releases latest/download/AIClockInSetup.exe. Actual changed files: README, RELEASING, RELEASE-0.5.0-READINESS, TASKS/HANDOFF/PROJECT/CHANGELOG. Documentation diff check performed; no app changes or rebuild/repeated regression needed. Publication supersedes earlier no-release/HTTP403 observations; other-PC compatibility and user-machine end-to-end install still unverified. Next: user tests update from an older installed version; an already-installed 0.5.0 correctly reports latest. Evidence outside repo: D workspace outputs/AIClockIn-validation/release-0.5.0/published-release.json and public-download/verification.json.
