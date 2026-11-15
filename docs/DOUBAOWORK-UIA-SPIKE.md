# TASK-022：签到页面 UIA 最小技术验证

## 直接运行

使用当前项目 Python，Windows PowerShell/UIAutomationClient 为系统组件，无新增依赖：

```powershell
python -B tools/probe_doubao_signin.py --restore --navigate --reveal --out "D:\AIClockIn-probes\before.json"
```

`--restore` 恢复已有窗口，不启动/重启客户端；`--navigate` 只选择已有活动标签或已暴露的应用活动菜单项，不调用活动页里的领取按钮；`--reveal` 只滚动“每日签到”文字进入视图。去掉上述开关可纯采样。每次最多3次默认采样，每次子进程20秒超时，节点数有上限。输出只保留限定业务文字和控件元数据，不保存整页、聊天、账号、凭据，结果恒为unknown而非伪造业务判断。

计划任务真实短时验证（创建唯一临时任务，完成后清理，正式任务不修改）：

```powershell
python -B tests/verify_doubao_probe_task_windows.py
```

## 本轮真实结果

1. 客户端实际正在运行，未重复版本/登录检查。首次页面读取出现 ElementNotAvailableException，HRESULT -2147220991；当时主窗口为Minimized，节点5/20。只读文本异常不再阻断对子元素的遍历；只对精确活动Document取文字，避免读取聊天。
2. UIA WindowPattern 恢复窗口至Normal后，取得约804个节点。SetFocus单独尝试被客户端拒绝，报目标无法接收焦点；没有把输出中的继续执行提示误认为聚焦成功。后续不依赖SetFocus即可读取。
3. 已有“免费用豆包工作”TabItem支持SelectionItem，可自动选择；“每日签到”支持ScrollItem，可滚动到可见。未确认无活动标签时如何从菜单可靠打开新活动页，不能承诺完全免人工导航。
4. 活动Document只有“每日签到”标签，未读到明确当前日期、已签/未签文字。签到横幅3次一致：10节点、6Group/4Text、Invoke=0、KeyboardFocusable=0，date/state标签均空。
5. 任务列表标题附近的“去完成”属于其他工作任务；三个禁用按钮属于额外里程碑奖励。没有把它们当作签到按钮或未签/已签证据。当前未唯一定位官方签到按钮；没有点击任何领取。
6. 当前仅有当天已经手动签到后的样本，无法证明未签到页面也没有按钮。缺少同账号、同日期的一次领取前后样本；不能重建今天的领取前状态或再领一次来验证。没有验证奖励到账转换。
7. 同一用户InteractiveToken、LeastPrivilege、未锁屏桌面下，3次真实独立计划任务执行均exit0，均读到活动上下文和同样横幅结构，临时任务已删除，正式任务XML保持不变。这里只证明短时采集/已开标签导航可运行，exit0不是签到成功，也不证明跨天长期稳定。

## 下一次有效样本怎样取得

下一自然日尚未领取时运行上述命令保存before.json；由用户在官方客户端手动领取一次（探针绝不代点），随后再次运行，保存after.json。需比较同账号/同日状态文本、控件可调用性和明确到账记录；金额差值或累计额不能单独作为到账证明。

如果未签到时暴露明确按钮和日期状态，UIA路径有继续实现条件；如果两种状态仍只有图形/无语义控件，当前UIA-only路径不足，需要客户端提供正常可访问性语义或其他受支持数据来源。当前不能承诺这一缺口一定可解。未来技术验证通过后，自动领取仍须满足平台许可条件；本轮不重复规则分析。

## 验证与文件

新增 tools/probe_doubao_signin.py、tests/verify_doubao_probe_task_windows.py、本说明。增量更新TASKS/HANDOFF/PROJECT/CHANGELOG，保留此前TASK-021未提交改动。AST语法检查和git diff --check通过；真实任务3次通过，未使用模拟状态替代真实签到。未改业务模块/数据库/账号/原平台/正式任务/安装包，无需全量回归或重打包；未提交、推送。

证据目录：D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/task022/，含初始失效样本normal.json、修正后normal-fixed.json、恢复后navigation.json、滚动后card.json和最终scheduled-results.json。失败阶段为“当日状态/按钮语义不足、缺未签对照及到账样本”，不是工具完全不能访问桌面。
