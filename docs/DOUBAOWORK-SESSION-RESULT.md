# TASK-025：客户端衔接预检结果（2026-11-15，部分完成）

本轮实现了独立启动/导航预检，尚未完成每日无人值守签到，没有重复今天领取。

## 实际文件及行为

- `aiclockin/doubao_session.py`：当前桌面会话检测、跨进程OperationLock、官方签名启动器定位、最多启动一次、90秒UIA子进程超时、真实SQLite记录。可见豆包号仅在内存SHA256，不当作已验证UID；未知金额NULL，每次独立观察不合并账号。
- `aiclockin/doubao_session.ps1`：Raw View、恢复最小化窗口、唯一账号菜单结构匹配、调用正式活动MenuItem、等候活动Document。无领取操作；异常仅输出类型/HRESULT，不输出客户端页面原文或凭据。
- `main.py`：新增互斥无GUI `--doubao-prepare`，冻结更新恢复期间同样拒绝执行；`--silent`和生产任务不变。
- `build.ps1`：加入PS桥接资源；本轮没有打包。
- `tests/test_doubao_session.py`、`tests/verify_doubao_prepare_windows.py`：隔离单元边界与真实临时计划任务验证。

开发者验证命令（仓库目录运行，不用于生产每日签到）：
```powershell
D:\Python\python.exe -B main.py --doubao-prepare --data D:\AIClockIn-prepare-test\data --report D:\AIClockIn-prepare-test\report.json
```
退出0也只表示预检准备完成，绝不表示领取成功。已发布v0.5.0不含此入口。未加入GUI开关或默认任务，避免提供虚假的每日签到功能。

## 真实计划任务证据

运行 `D:\Python\python.exe -B tests/verify_doubao_prepare_windows.py`。无AIClockIn GUI进程，当前用户InteractiveToken、独立数据库、唯一临时任务；证据根目录为 `D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/task025/`。

|场景|子目录/result.json及结果|
|---|---|
|已开，初版导航|0b4a26f95ad0：activity_unavailable，菜单调用返回但无活动Document|
|用户保存并正常退出，确认进程0，任务冷启动|ba197e879ea4：launch_started=true，官方启动器正常启动一次；随后activity_menu_missing，未通过整链路|
|启动后多任务卡片已加载，宽泛控件条件|3bbdd8d23571：多个radix控件导致无法唯一识别账号菜单，失败|
|改为账号菜单实际Image/Group/Image子节点约束|92a1f4bdf1e4：活动菜单正常导航并读到Document，但无账号号，identity_unknown|
|先正常最小化，再运行最终导航条件|5be89ac1e63d：restore/account_menu/activity_menu，活动Document已读，identity_unknown|

这些任务均退出1，真实记录失败，不领取；临时任务均清理，生产任务XML前后相同。当前页面未预先保留活动标签的场景已走通菜单导航，但最终条件下再次完全退出→导航的整链路尚未复测通过。没有把客户端启动成功视为每日签到成功。当前无签到按钮不等于今日已签到。

## 自动化、审查和保护

- `D:\Python\python.exe -B -m unittest discover -s tests -p 'test_*.py'`：107通过，其中新增9项受控测试；不是107次真实签到。最后新增activity_ready报告字段后复跑相关9项，通过。
- 新测试覆盖不重启/最多启动一次/锁屏不启动/账号不匹配/身份缺失不误报登录失效/明确登录要求/异常不泄漏/菜单失败/超时。
- PS `Parser.ParseInput(Get-Content -Encoding UTF8 -Raw ...)`：0语法错误。PS5直接ParseFile读取无BOM源码会误解中文；运行桥接使用UTF8读取、D盘UTF8 BOM临时文件。
- `git diff --check`：通过。审查修正同会话过滤、菜单歧义、加载阶段提前退出和错误输出。providers/auth/service/store/schedule核心文件无diff。
- 本机真实定位了官方启动器，签名Valid、预期发布者；未安装/更新/退出登录客户端，未修改数据库结构、原账号或安装更新机制。

## 仍受限及下一步

1. 早期菜单中可读取候选豆包号指纹，最终导航测试未读到，故保持身份待确认，不合并历史、不自动领取。
2. 当前已领页面无法可靠确认当天状态，保持unknown；累计额度和无按钮均不用于推断。
3. 新入口锁屏仅受控测试；此前真实只读锁屏失败限制保留。登录失效没有人为退出账号实测，不把缺字段误报为失效。
4. 独立源码计划任务实际执行和SQLite持久化已验证；EXE/安装包、完整冷启动→身份→当日状态→领取→到账链路未验证，不启用每日领取。
5. 下一步解决最终活动导航下稳定可见账号标识/绑定和当天状态证据，再重验冷启动整链路。平台许可仍按用户本轮条件作为领取门槛；今天不重复领取。现阶段不能承诺完全无人值守签到。
