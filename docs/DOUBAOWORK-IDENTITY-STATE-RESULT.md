# TASK-026：账号身份与当日状态证据复核

2026-11-15（北京时间）。本轮不领取、不打包、不发布，不修改原平台核心、生产任务或生产数据库。

## 两个阻塞的实际结论

|问题|本轮结论|
|---|---|
|当前账号身份|解决了“可见豆包号读取不到”的一个具体环节：官方设置对话框内可读。尚未完成正式绑定及换号实测，不能宣称稳定UID已验证|
|今日签到状态|未解决通用当日状态识别。历史样本可以确认那一次真实成功，但没有业务日期和可靠账号绑定，不能扩展成重启后当前账号的今日状态|

## 真实账号读取证据

头像菜单并不总向UIA暴露豆包号；正常调用唯一“设置”Button后，设置对话框中的Button可访问名称包含可见豆包号。读取被限制在对话框祖先内，不从聊天内容提取身份。仅在内存对账号号做SHA256，未知、多值、异常均不补齐，不保存明文。完成后仅尝试关闭该对话框内唯一的“关闭”Button。

新增 `Read-VisibleIdentity` 和 `ClientBackend.inspect_identity()`；重复验证命令：
```powershell
D:\Python\python.exe -B tools/verify_doubao_identity.py --out D:\AIClockIn-identity-evidence.json
```
要求官方客户端已运行、桌面解锁；不会启动新客户端、登录、换号或领取。证据文件拒绝覆盖。

真实证据根目录：`D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/task026/`。

- `identity-settings-repeat.json`：10:17连续两次读取同一候选指纹。
- `identity-final-repeat.json`：10:21最终验证工具连续两次读取同一候选指纹，`same_visible_number=true`、`identity_verified=false`。
- 该指纹与TASK-025中重启前记录的候选指纹一致。这仅是同一可见账号号的重复性证据，不证明平台承诺其不可修改，也未进行真实换号试验。
- `preflight-report.json`：试验性串联设置读取与活动导航时，取得账号指纹但活动Document未读到，明确失败。故**最终代码不在默认导航中插入设置读取**，保留独立验证接口，避免未验证串联影响既有流程。

### 用户确认的单账号模式

可考虑让用户在官方可见资料页确认当前账号号，并绑定候选指纹，明确标注“用户确认绑定，非平台UID验证”。执行前和提交后必须重新读取同一可见字段；字段缺失、冲突或变化立即停止，不用昵称、旧缓存或一个“已确认”勾选框代替身份检查。该方案不能解决字段不可读时的换号检测，也不能补上业务日期。真实换号检测、账号号是否可修改、设置读取与活动导航串联仍未验证，本轮未创建正式绑定或启用领取。

## 真实签到前后样本复核

来源TASK-023目录 `20261115/auto-once-before.json`、`auto-once-after-001.json`、`auto-once-attempt.json`。新增可重复审计工具，输出原文件SHA256，不修改样本：
```powershell
D:\Python\python.exe -B tools/audit_doubao_samples.py --samples <原始样本目录> --out D:\AIClockIn-sample-audit.json
```

实际输出 `task026/historical-audit.json`：

|证据|签到前00:23:12|签到后00:23:56|
|---|---|---|
|完整UIA节点|239，未截断|251，未截断|
|唯一实际签到按钮|Button“立即签到”，可见、enabled、Invoke、focusable|不存在|
|即时成功提示|无|可见Text“签到成功”和ListItem“签到成功查看奖励”|
|业务日期节点|未发现|未发现|
|账号绑定|identity_verified=false|identity_verified=false|

一次性尝试账本时间00:23:55位于前后采样之间，max_invocations=1；审计确认有序单次成功转变，不仅凭累计变化或Invoke返回。前按钮automation_id/help/status为空，后提示是瞬态。样本beijing_day由采集器写入，不是服务端业务日期。累计200→400只能作辅助数据，不作为状态判据。当前日常判定仍unknown。

当前页面补采：`current-state.json`没有活动Document，capture_ok=false，原样保留，未拿旧样本替代。随后正常UIA导航到官方额度管理页，`quota-state-evidence.json`实际读到“额度消耗明细”，没有签到文本、奖励/领取记录标签及日期token；不能把余额当签到状态。此结论仅针对当前暴露的UIA信息，不代表平台服务端不存在这些数据。

## 具体还缺什么

1. 账号：完成用户确认绑定（若采用此模式）、不同账号切换时的真实停止验证，以及设置读取/活动导航/再次身份复核的可靠串联。不能把四次相同指纹当成已验证跨账号安全。
2. 已签到：需要当前账号、当天业务日期对应的持久已签标识，或官方可见签到奖励流水（账号、日期、奖励），并验证刷新/重启后仍有效。临时Toast不足以回答之后的今日状态。
3. 未签到：现有唯一Button是可操作候选证据；还需与可靠业务日期/新鲜状态和账号绑定关联，不能直接把采集器本地日期当平台日期。
4. 如果客户端UIA始终不提供这些状态/日期，单靠当前UIA树无法满足严格判定要求；需要官方提供/显示可读取状态或奖励流水。重复采集同样无日期的页面不会自动补齐证据。
5. 平台允许方式、上述身份/状态门槛确认后，才验证完整启动→导航→身份→查重→一次领取→到账→持久化；当前未知即停止，不重复今天领取。每日无人值守仍未完成。

## 文件与测试

代码：`aiclockin/doubao_session.ps1`、`aiclockin/doubao_session.py`、`tools/verify_doubao_identity.py`、`tools/audit_doubao_samples.py`；测试：新增`tests/test_doubao_sample_audit.py`，增补`tests/test_doubao_session.py`。

- `D:\Python\python.exe -B -m unittest tests.test_doubao_sample_audit tests.test_doubao_session`：15通过。新增审计模块先运行得到模块缺失失败，再实现后通过；是受控边界验证，不是真实签到。
- PS `Parser.ParseInput(Get-Content -Encoding UTF8 -Raw ...)`：0语法错误。
- `git diff --check`：通过。providers/auth/service/store/schedule无diff。
- 未重复全量打包/安装或平台请求：本轮仅独立诊断与身份读取辅助接口，没有启用领取或修改生产分派。
- 原有未提交内容保留，无Git提交/推送。本轮结果及限制同步TASKS、CHANGELOG、HANDOFF、PROJECT。
