# AIClockIn 项目规范

- 豆包工作最终目标为每日自动签到、查重、到账复核和记录，现有只读查询仅为阶段基础。平台许可、可靠账号/当日状态及到账证据未确认时，不实施领取或宣称已完成自动签到；当前准入结论见 docs/DOUBAOWORK-AUTOCHECKIN-GATE.md。
- TASK-024：用户最新明确要求已授权当前账号单次官方UIA签到验证，已真实执行一次并回查成功。此次授权不等于开启每日任务、多账号或重复领取；保留一次性账本，当前日不得为测试再次领取。证据见 docs/DOUBAOWORK-AUTO-ONCE-RESULT.md，已发布v0.5.0不因此自动变为每日签到版。

- 本项目为独立 Git 仓库；不要修改 AICreditPunch / DailyCheckin 的代码、账号或任务。
- 用户已确认：WorkBuddy / Trae CN、多账号、一键顺序签到、简单记录、全新 Tkinter 中文界面，保留独立后台定时签到。
- Python 标准库 + Tkinter，Windows x64。不增加推送、代理轮换、设备模拟、手动快照导入或复杂积分报表。
- 独立编写应用结构、HTTP 客户端、结果模型、存储、GUI 和任务管理；必要 WorkBuddy 本机登录适配可带 MIT 声明复用，不整体搬入旧脚本。
- 账号 DPAPI 当前用户加密，SQLite 历史不含凭据。错误不记成成功；9095 立即记录设备受限，不绕过服务端规则。
- 所有新增文件、依赖、缓存和解压路径放 D 盘。数据与程序分离；TASK-008 已授权 PyInstaller 文件夹版 + Inno Setup，更新完整程序目录，绝不打包或覆盖 data。原生 Setup 的临时解包遵循 Windows TEMP，不能承诺所有机器固定 D 盘。
- TASK-005 已获用户明确授权：安装时创建当前用户桌面快捷方式，按 Windows 实际桌面路径写入单个 .lnk（桌面可能位于 C 盘）；程序、数据、安装暂存仍只放 D 盘。已有安装保留 EXE/data/任务路径，不自动迁移账号。
- 自动任务名 AIClockIn-Auto，直接运行本项目 EXE --silent；不迁移或删除旧软件任务，不自动转移旧账号。
- 文档映射：需求/架构/重要决策合并于 docs/PROJECT.md；任务 docs/TASKS.md；变更 CHANGELOG.md；交接 docs/HANDOFF.md；实施步骤 docs/PLAN.md。
- 本项目编号从 TASK-001 开始，与其他项目独立。Git 可初始化；无自动提交、推送、改远程授权。
- 最小充分验证：平台协议 mock、加密与历史、GUI 默认/小窗口、打包自检；不以 mock 通过宣称真实签到成功。

## TASK-030 current release scope
User formally stopped Doubao development. Stable builds hide its UI and exclude research modules, retaining sources/data/history. Do not restart probes/sampling. Official functions are WorkBuddy and Trae CN; preserve their core and schemas. v0.5.1 local package and actual validation: docs/STABLE-0.5.1-RESULT.md. No automatic commit/push/publication authorization.
