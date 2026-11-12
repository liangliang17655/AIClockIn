# AIClockIn 项目规范

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
