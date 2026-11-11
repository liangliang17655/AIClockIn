# 交接

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
