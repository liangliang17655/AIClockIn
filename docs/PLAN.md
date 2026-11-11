# TASK-001 实施步骤

已获用户确认，直接在本独立仓库实施；不再修改旧项目。

- [x] 1. 核心 mock / DPAPI / 历史 / 服务已实现，测试先失败后通过。
- [x] 2. 正常 WorkBuddy 导入与 Trae 浏览器授权已实现；有限 MIT 登录适配有明确声明。新项目真实授权未验证。
- [x] 3. 独立单任务、绝对 EXE 和数据路径、操作锁及独立 worker；Windows 临时名称实测通过并清理。
- [x] 4. 全新中文界面与图标完成，默认 1080×780 和最小 920×660 截图检查通过，无快照入口。
- [x] 5. 20 项全量测试通过；独立审查问题已修复复核；D 盘打包、安装 EXE 自检及复制到独立目录运行通过。
- [x] 6. README、许可、来源、任务及交接完成；本地 Git 初始化，敏感和产物排除；没有提交或推送。

接口契约：Outcome(state, earned, balance, detail)；Provider.run(account,status_only=False)；Store.accounts()/save_accounts()/record()/history()；Service.run()/import_workbuddy()/login_trae()。所有历史通过本地 UUID 绑定账号，不通过昵称绑定。

重点：9095 不是账号成功；认证错误/余额未知不得伪装；配置损坏不覆盖；重登不丢账号 ID；后台无 GUI 依赖；新旧任务互不修改；截图只用合成数据。
