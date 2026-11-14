# 交接

## TASK-007 · 2026-11-11 · Trae CN 能力文案纠正

用户指出 README 宣传 Trae CN 多账号签到与实际限制不符。已修改 README.md 顶部、产品介绍和 Trae CN 使用步骤，明确“同设备多账号领取限制尚未解决”，区分保存/管理多个凭据与多个账号均能领取；同步 docs/PROJECT.md 的实际能力边界、TASKS.md、CHANGELOG.md 和本节。未删除多账号管理，未改签到逻辑、平台接口、账号数据或 EXE。

实际验证：核对 providers.py 的 9095 分支仍返回设备受限；rg 检查 README 中原无条件多账号宣传已移除，git diff --check 验证格式。没有运行软件测试或打包，因为仅为文档修正且业务代码无变化。仍未解决/未验证 Trae CN 同设备全部账号每日领取，不能将历史 mock 测试通过作为此能力的证明。

## TASK-006 · 2026-11-11 · v0.3.1 设置与快捷方式

用户要求优化设置样式，随后澄清是 GitHub 下载的 EXE 双击无响应，并提供“Windows 已保护你的电脑 / 发布者未知 / 仍要运行”截图。接入时工作区干净、main 与本地 origin/main 均为 b5bcf14，用户已同步上一阶段代码；旧 TASK-005 的远程失败为历史状态。本次分支 fix/settings-startup。

调查：原 EXE 本地启动能显示主窗口；匿名 HTTPS 实际重新下载 GitHub main EXE，200、14,095,515 字节、SHA256 31bbe9344a75719ade38b6262ef9cda762411172f23e138a08119ebf21c421e7，与原本机一致；通过系统关联启动该下载副本约 1 秒出现安装窗口。Authenticode=NotSigned；用户截图确认 Windows 在程序启动前给出 SmartScreen 提示，已说明核对来源后“更多信息 → 仍要运行”。用户本人确认运行后能否打开尚未收到答复；不标记该用户操作已验收。签名未配置，不能声称 Windows 提示已被代码消除。

实际文件：新增 aiclockin/settings_menu.py、tests/test_settings.py、tests/preview_settings.py、tests/verify_settings_windows.py、docs/SETTINGS-FIX.md；修改 aiclockin/update_gui.py、gui.py、VERSION、AIClockIn.exe、README.md、tests/test_update_gui.py 和任务/项目/变更/交接记录。原因：用统一浅色弹层替换默认灰菜单，创建桌面链接改为后台直接调用现有安全创建函数，明确成功/错误，不再拉起安装向导；不改安装核心、签到接口、存储和任务逻辑。

实际验证：python -B -m unittest discover -s tests -v，60 项通过（原 55 + 新增 5）；新增行为先失败后实现，另修复弹层 Esc 需要明确焦点的问题。python -B tests/preview_settings.py 默认/紧凑主界面及弹层截图已检查。release.ps1 复用已有 D 盘 PyInstaller 构建并通过 EXE 离线自检。python -B tests/verify_settings_windows.py 对冻结 EXE 实际鼠标点击菜单及第三项，冲突显示“创建快捷方式失败”；部署后 python -B tests/verify_settings_windows.py --existing 同路径实际点击，弹出“桌面快捷方式已创建”，验证冻结 PowerShell 路径，而非只验证源码 mock。两者均关闭自己启动的窗口，没有签到请求。

本地项目根及桌面目标已更新至 0.3.1，SHA256 8985e7bb13d9011ef422489da1ec51402a1d1af5eb8957ca8fe6ce68c9fe2134，实际账号/数据库等文件哈希及 AIClockIn-Auto XML 未变。证据目录 D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/settings/，含 deployment.json、frozen-success.json、frozen-conflict.json、默认/紧凑截图。GitHub 下载调查副本位于 D 盘 temp/AIClockIn/download-repro，不写 C 盘程序文件。

独立审查未发现 Critical/Important，并额外验证真实 press/release、菜单操作和移焦关闭。次要未补项：连续两次点击只创建一个线程没有独立自动测试；同步 creating_shortcut 防重入已代码核对。未做二次审查。未验证：用户机器确认“仍要运行”之后的实际结果、可信签名/发行信誉、实体断电、真实 GitHub Release 在线升级。SmartScreen 微软依据见 README 链接。

本阶段实际保留现有安装逻辑；此前考虑首装异步查询，但明确 Windows 提示后未做无关启动重构。不自动发布 Release、不购买证书、不改变 Windows 安全设置。

用户继续要求同步后，定位 Git 网络差异：当前 Windows 启用了本机 HTTP/HTTPS 系统代理，而 Git 原先直连 GitHub 失败。仅对推送/核对命令通过 -c http.proxy 使用现有系统代理并保留 HTTPS 证书验证，未修改任何持久 Git/系统代理配置。git push origin main 成功（b5bcf14..0045103）；使用同一路由 ls-remote 确认远程 main=00451034cb019526c8ad7962a79abb3ef5655623，本地与远程一致。

再次匿名 HTTPS 下载 README 中 main 分支的实际 EXE 直链：HTTP 200、14,102,080 字节、SHA256 8985e7bb13d9011ef422489da1ec51402a1d1af5eb8957ca8fe6ce68c9fe2134，与本地 v0.3.1 完全一致。代码/下载同步已完成；仍不等于创建 GitHub Release 或消除 SmartScreen。此轮只补交付文档，不重复软件回归/打包，因为程序文件未变化；文档运行 git diff --check，最终提交随代码一并同步。

## TASK-005 · 2026-11-11 · v0.3.0 安装与桌面入口

用户已确认固定 D 盘目录和桌面入口。实现同一 EXE 内安装窗口，不引入安装器框架/依赖，不增加第二份运行时。新用户默认 D:/AIClockIn；已有用户识别源旁 data、当前用户自动任务或默认目录已有数据，保留原 EXE/data 路径。设置新增“创建桌面快捷方式”，补建后关闭安装窗口，不重复打开主窗口。

实际文件：新增 aiclockin/installer.py、tests/test_installer.py、tests/test_installer_gui.py、tests/verify_install_windows.py、tests/preview_install.py、docs/INSTALL-PLAN.md；修改 main.py、aiclockin/update_gui.py、VERSION、项目根 AIClockIn.exe、README.md、AGENTS.md 及 docs/PROJECT.md、RELEASING.md、TASKS.md、HANDOFF.md、CHANGELOG.md。原因：让用户从桌面使用，安装/重复安装保护账号和原任务，不改签到核心。

实际验证：python -B -m unittest discover -s tests -v 共 55 项通过；release.ps1 复用 D 盘既有 PyInstaller 6.22.3 构建并通过离线版本/加密/数据库/Tk 自检；python -B tests/verify_install_windows.py 通过真实冻结首启（创建 Store 前显示安装、取消退出码 1）、新目录安装、实际 .lnk 启动主 GUI、自定义 --data、重复安装数据哈希/解密、不同目标链接保护、旧版原地升级和唯一临时任务升级后执行（无启用账号退出码 1）/XML不变/清理。python -B tests/preview_install.py 最小尺寸新装/已有窗口截图已检查。测试未调用真实平台签到。

一次独立审查指出默认目录已有数据但未开启任务的识别遗漏；已补先失败后通过回归。并发覆盖链接问题提升为必修，使用两个同步 PowerShell 进程复现，再改 .NET 原子无覆盖 Move；补入口后多开主窗口也已修复。三个回归先失败后通过，最终全量 55 项通过。集成脚本曾在链接启动后观察 PowerShell 进程遇到 WinError 5，改为原生 Win32 查询/关闭测试副本，并等待全部退出，最终完整验证通过；未据此推断平台或用户系统故障。未派发二次审查。

已部署项目根 0.3.0：SHA256 31bbe9344a75719ade38b6262ef9cda762411172f23e138a08119ebf21c421e7，14,095,515 字节。真实桌面 C:/Users/sq/Desktop/AIClockIn 自动签到.lnk 指向原 D 盘项目 EXE，并保留原 --data。实际账号/数据库等文件哈希和原 AIClockIn-Auto XML 前后完全相同；未迁移到 D:/AIClockIn，以免改动已有账号/任务路径。证据在 D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/install/（windows-install.json、deployment.json、new.bmp、existing.bmp）。

风险/未验证：真实 C 盘下载来源未新建 EXE 做测试（遵守存放偏好），C 盘路径由启动路由单测覆盖，真实来源使用 D 盘隔离副本；当前 Windows 用户的 C 盘桌面快捷方式已实际创建。其他 Windows 用户/重定向桌面环境、实体断电、真实 GitHub Release 升级仍未验证。安装不自动开启定时签到；用户仍需在主界面点击开启。源码 Git 提交/推送与正式 Release 发布分开，不能把本地构建当成已发布 Release。

Git 交付：沿用用户前序提交远程授权，功能已本地提交 18f0b0e。git fetch origin 遇连接重置，git push origin HEAD:main 遇 github.com:443 连接失败；尚未推送，因此远程下载入口暂未获得本次 0.3.0。下一步网络恢复后同步 main，不能声称线上已更新；本机部署与桌面入口不受此网络失败影响。

## TASK-004 · 2026-11-11 · README 直接下载

用户要求下载入口名称易懂、点击直接下载，不再进入 Release 页面。修改 README.md 顶部为“点击下载自动签到软件（Windows 电脑版）”，指向仓库 main 分支已跟踪 AIClockIn.exe 的 raw.githubusercontent.com HTTPS 二进制地址；下载名称就是 AIClockIn.exe，移除寻找 Assets、重命名及未发布 404 的旧说明。仅更改下载文档及本次 TASKS/CHANGELOG/HANDOFF 记录，不改变应用更新源或程序行为，不创建 Release。

实际验证：匿名 HTTPS HEAD 返回 200，Content-Type 为 application/octet-stream，Content-Length 14071703，与本地已验证 EXE 大小一致。git diff --check 检查文档；不重复运行软件测试或打包，因为应用代码和 EXE 未变。

边界/下一步：README 直链随 main 中的 EXE 更新；软件内自动更新仍只从正式 GitHub Releases 获取，真实线上更新待正式发布后验证。浏览器是否弹出保存位置由用户浏览器设置决定。后续维护者若不再在 Git 中跟踪 EXE，应同时改为已发布且存在的 Release 附件直链，不能恢复成发布列表页面。

## TASK-003 · 2026-11-11 · 用户授权提交远程

目标：提交已交付 v0.2.0 至公开仓库并写清提交说明。执行前 git fetch 确认 origin/main 与开发基线 016521d 相同，无远程冲突。功能提交 a2f9f6d（feat: 发布 v0.2.0，新增 GitHub 自动更新功能）已从 feature/github-updater 快进合入 main，git push origin main 成功，输出 016521d..a2f9f6d main -> main。当前工作分支 main，保留开发分支，未强推或删除分支。

提交包含 TASK-002 的代码、测试、发布工具、README 下载入口及原已跟踪 EXE；完整文件映射见 UPDATE-VALIDATION.md。本次补充记录文件为 docs/TASKS.md、docs/HANDOFF.md 和 CHANGELOG.md，原因是记录用户明确授权后的 Git 交付，不改变应用行为。

提交前重新运行 python -B -m unittest discover -s tests -v：43 项通过；git diff --cached --check 通过；暂存清单无 data、账号、数据库或日志。提交正文说明更新机制、数据保护、验证及线上升级未验证边界。未重复打包或运行隔离 EXE 测试，因为程序代码和已验证产物未发生变化。

风险/下一步：代码推送不等于发布正式 Release；未打标签或上传 Release 附件，真实 GitHub 端到端升级仍待维护者按 RELEASING.md 发布后验证。下方 TASK-002 的“未提交”表述属于当时本地交付阶段历史状态，以本节为最新 Git 交付记录。

## TASK-002 · 2026-11-11 · v0.2.0 本地交付

用户确认 [自动更新方案](UPDATE-DESIGN.md) 后实施，并追加 README 直接下载安装入口。代码位于本地 feature/github-updater 分支，基线 016521d；没有自动提交、推送、打标签或发布。完整修改清单和逐项实测见 [UPDATE-VALIDATION.md](UPDATE-VALIDATION.md)，发布步骤见 [RELEASING.md](RELEASING.md)。

当前 VERSION 和项目根 AIClockIn.exe 已为 0.2.0，仍为 PyInstaller Windows x64 便携单文件。正式附件在 dist/release/v0.2.0/：AIClockIn-v0.2.0-windows-x64.exe、SHA256SUMS.txt。SHA256 9badc04a53c48b8c0445b99c6402aba5d3ba9283bfeda22845156008038aca9b。

设置包含手动检查、自动检查开关、关于。GUI 启动后台检查正式 Release；静默签到和离线自检不检查。新版本读取远程说明，下载/校验后要求确认安装；本机独立辅助 EXE 等待旧进程退出，替换原路径，再用合成数据健康检查、失败恢复、重启并保留原 --data。

数据保护：原 data/accounts.json、history.db 等扁平路径不迁移；更新偏好独立 update-settings.json。签到核心 providers/auth/workbuddy_auth/store/service/schedule 源文件哈希保持原值。实际本地部署时等待原窗口关闭，在更新锁/操作锁内替换，并核对全部实际数据文件（排除正持有的协调锁文件）哈希及生产 AIClockIn-Auto XML 完全不变，没有触发真实签到。

实际验证：43 项 unittest 回归全部通过；release.ps1 构建及离线版本/DPAPI/历史/Tk 自检通过；verify_update_windows.py 真实隔离替换和自动重启、合成数据哈希/解密、唯一临时任务 XML 不变及升级后执行/清理通过；verify_health_timeout.py 专用冻结嵌套卡死 EXE 的进程树超时清理与恢复通过；preview_update.py 截图已检查。一次独立审查的两项 Important 已修复并补测试，无二次审查。具体命令/证据边界见验证文档。

证据在 D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/update/，含 windows-update.json、frozen-timeout.json、deployment.json 和合成截图。部署旧版备份：D:/个人开发软件/AI工作区/temp/AIClockIn/updates/6c325cb362bf4ed2b5ce936655476f1a/previous.exe，不自动清理。

未验证：真实 GitHub 互联网下载/升级（初期查无正式 Release，末期匿名请求 403）、实体断电/硬件故障/防病毒隔离、真实平台领取。旧 v0.1.0 用户要先手动换一次 EXE。下一步由维护者提交/推送、按发布文档上传正式附件和说明，再用隔离用户副本完成线上升级验收。此状态不表示线上发布已完成。

## TASK-001 · 前序交付记录

TASK-001，2026-11-11：独立应用 v0.1.0 已交付。仓库 D:/个人开发软件/国产AI自动签到/AIClockIn 已 git init -b main，没有提交或远程。目录接入时为空。

用户已确认功能范围及保留后台签到。源代码、UI 和数据在本项目独立开发；旧项目的未提交改动保留，不继续修改，旧应用和任务保持原样。

产物：项目根目录 AIClockIn.exe（14,037,486 字节），SHA256 aa576b9088518a7bc07e8f2a522750449f29ae3d1d0ffabcdcc61ca985b960d7。应用运行不依赖旧仓库或外置 Python。打包时复用已存在的 D 盘 PyInstaller 工具环境，构建/缓存/解压产物位于 D 盘。没有整体搬入旧签到脚本，仅 workbuddy_auth.py 为明确署名的 MIT 本机登录适配。

实际文件：aiclockin 下 models/http/providers/store/auth/workbuddy_auth/service/runtime/schedule/gui/__init__ 模块、main.py、assets/app.ico、build.ps1、requirements-build.txt、VERSION、tests/、README/许可/来源、AGENTS.md、docs/、.gitignore 与 CHANGELOG。原因：落实独立精简签到应用、全新 UI、本地版本管理及后台执行要求。

实际验证：
- `python -B -m unittest discover -s tests -v`：20 项通过，覆盖核心状态/回查、9095、未知状态不领取、账号密文与历史、锁、服务逐账号继续、重登录保持 ID、任务事务、GUI。
- `python -B tests/preview.py`：1080×780 / 920×660 合成数据截图已检查。截图不使用真实账号，输出位于 D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/。
- `build.ps1 -BuildPython <已有D盘隔离Python>`：单文件无控制台 EXE 构建成功。
- `python -B tests/verify_windows.py`：安装版离线加密/历史/Tk 自检通过；复制 EXE 到独立临时目录后，以唯一 AIClockIn-Test-* 名称创建、触发并移除任务；自定义带空格数据目录正确使用，空账号退出码 1，没有伪装成功；任务清理验证通过。
- GUI 父进程退出后独立 worker 继续完成离线自检，验证通过。
- 独立审查修复 token 主体与账号不匹配、自定义数据目录在任务中丢失两项 Important，并补先失败后通过的回归；复核未发现 Important。
- Git 忽略规则核验、git diff --check 和文档链接检查在收尾执行；不自动提交或推送。

未验证及原因：新项目真实 WorkBuddy 导入、Trae 授权和实际领取未执行；没有自动迁移用户旧账号或以真实账号做测试。真实登录/恢复系统事件触发未进行人工休眠测试。模拟与空账号任务通过不能证明真实平台奖励资格或接口永久可用。

当前数据与自动状态：新项目没有真实账号，生产 AIClockIn-Auto 未注册；初次打开需添加账号，点击“开启自动签到”。旧 DailyCheckin 账号、源码和生产任务没有在新项目开发期间修改，旧自动任务仍可能运行。切换使用时请用户在旧软件中停用，避免两套应用同时操作同一账号。

下一步：用户双击 AIClockIn.exe 体验新界面并添加自己的账号进行真实验收；若需要迁移旧账号或替换旧自动任务，另行明确授权。后续上传 GitHub 时只提交被忽略规则允许的源码/文档/测试和许可，EXE 可放 Releases，绝不提交 data。


## TASK-008 · v0.4.0 原生安装包

已本地生成根 AIClockInSetup.exe；72 项回归及真实隔离安装/升级/卸载和完整辅助更新通过。未推送、未发布 Release、未改用户生产安装/任务。完整文件清单、命令、结果、限制和下一步见 [TASK-008 验收](INNO-PLAN.md#task-008-实际交付与验证2026-11-12)。旧0.3.x首次需手动 Setup，签名与线上更新仍未验证。


## TASK-009 · 2026-11-12 · 提交 v0.4.0 与更新下载说明

用户明确授权提交并推送远程。更新 README 的原生安装包直链、安装及旧版迁移说明；补充 .gitignore 排除本地安装依赖和卸载元数据。发布已验证的根 AIClockInSetup.exe，不提交本地已安装的 AIClockIn.exe 改动、data 或运行目录。TASK-008 的源码、测试及文档一起交付。远程核对 origin/main 基线仍为 9843ae8，无新增远程提交。

验证沿用 TASK-008 最新72项回归及原生安装/更新测试（业务代码未再改动）；本次执行 git diff --check、暂存清单检查、安装包 SHA256、远程提交核对与直链下载校验。未创建正式 Release；软件内线上更新仍待正式发布后验证。提交/推送结果以 Git 历史和最终交付报告为准。


TASK-009 远程结果：功能提交 `1a4400b` 已快进合入并推送 origin/main，ls-remote 核对一致。README 固定 Setup 直链 HTTP 200，13,848,776 字节，SHA256 与 TASK-008 本地产物一致。暂存检查未包含 data、安装依赖、卸载元数据或本地已安装 AIClockIn.exe 改动；后者保留工作区未提交。未创建正式 Release，线上自动更新仍待发布后验证。


## TASK-010 · 2026-11-12 · 卸载重装后账号不可见与添加提示排查

状态：数据路径已本机恢复；添加提示原因仍待用户复现确认，未声称已修复。

事实：旧项目 data/accounts.json 中3个账号仍在，并能由当前用户解密；新安装 D:/AIClockIn/install-info.ini 指向 D:/AIClockIn/data，后者没有 accounts.json。不是已证实的账号删除，而是安装位置变化后读取了新目录。两处 operation.lock 均可实际获取，未发现持续占用。安装版在独立合成空目录执行 --silent 可取得锁并如实返回“请先添加并启用至少一个账号”；没有请求真实平台。

修复：备份 D:/AIClockIn/install-info.ini 到 D:/个人开发软件/AI工作区/temp/AIClockIn/recovery/20261112-100153/；将其 Data/Directory 改回原项目 data，调整已有且目标匹配 D:/AIClockIn/AIClockIn.exe 的桌面链接数据参数，正常关闭/重开GUI。原目录所有数据文件哈希修改前后完全一致，3个账号解密验证通过；新目录不删除，未迁移/覆盖账户，未修改签到任务和源码。系统集成变更按用户故障修复请求执行，路径未进入公开日志。

实际验证：数据目录解析、3个账号解密、数据文件SHA256不变、两个目录OS字节锁探测、安装版隔离空账号 --silent（exit1真实无账号提示）通过。未执行真实签到或账号授权；原GUI重新打开后账号可见性及添加操作等待用户确认。后续需复现添加操作的具体平台和进程状态，再针对根因补回归；不直接删除锁或强杀进程。


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


### TASK-012 追加排查

用户确认缺失前执行了“卸载旧版、运行新版Setup”，未提供旧卸载日志。以当前安装脚本、独立AppId和D盘临时运行目录重放：在安装位置预置main.py、aiclockin/gui.py、.git/HEAD、未跟踪notes.txt与模拟账号/历史，实际原生安装再卸载，逐文件存在性和SHA256均保留，通过。证据位于D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/inno/source-safety.json和source-safety-install/uninstall.log。隔离编译复用当前完整运行目录，不请求平台、不操作生产卸载键或任务；独立数据位置登记测试后清理。

结论边界：当前安装/卸载规则未复现源码清空，不等于证明用户先前操作无问题，也不能据此指定删除责任。未找到对应旧卸载的本机日志；删除根因仍未确定。源码已从远程恢复，当前运行目录D:/AIClockIn与源码目录分开；此次未改业务代码或发布新包。后续若拿到旧卸载器/日志，再对照其登记范围，不能直接在真实源码上重放卸载。


## TASK-013 · 2026-11-14 · 安装自检跨电脑失败诊断修复

根因证据、影响范围、完整修改清单与测试边界见docs/INSTALL-DIAGNOSTICS.md。已确认旧安装器{tmp}报告在C时被main的D盘约束拒绝，且异常被通用提示掩盖；首次失败留下启动文件也已复现并修正。版本0.4.2保留自检/版本/失败恢复，增加D盘阶段诊断、90秒原生进程等待与句柄关闭，安装版.runtime不再依赖开发机目录；selfcheck禁用网络和任务探测。签到核心和生产账号/任务不改。

实际文件：.gitignore、VERSION、main.py、aiclockin/selfcheck.py、runtime.py、gui.py、installer/AIClockIn.iss、tests/test_selfcheck.py、verify_install_diagnostics_windows.py、docs/INSTALL-DIAGNOSTICS.md、TASKS/HANDOFF/CHANGELOG、根Setup及后续README下载说明。保留原TASK-012未提交恢复记录。

验证：78项unittest通过；build与release exit0；真实原生超时/版本不符恢复旧4.1哈希、合成账号/SQLite/历史、任务XML保持；故意缺_tkinter依赖输出类型/阶段/堆栈且首次失败EXE清理；首装桌面/开始菜单、正常GUI/.runtime及卸载自有链接通过。独立审查发现终止状态检查问题已修复，原生进程实现复核通过。其他实体电脑、Defender隔离、真实C-TEMP启动原生Setup均未实测。未关闭防护，未发布正式Release。下一步由对方复测并提供诊断文件，远程分发结果以最终提交记录为准。


TASK-013 远程分发：修复与安装包提交 `2f263c2` 已推送 origin/main；固定提交下载 HTTP200，13,855,332字节，SHA256 65da9bdae4c7dca82b186e37942f4567147567ec3bd2c46f3985c237da7b4ae0，与最终本地Setup一致。README版本和下载链接同步v0.4.2，避免main缓存旧包。未创建正式Release，等待对方电脑复测；本机生产安装没有被自动替换。


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
