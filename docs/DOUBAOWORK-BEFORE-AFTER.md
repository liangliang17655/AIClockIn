# TASK-023：下一活动日真实前后对照（进行中）

## 当前进度

已提供采集和差异工具；真实未签→手动签到→已签对照尚未产生，不能据今晚样本推导状态识别模块。保留原 tools/probe_doubao_signin.py，新增 tools/doubao_compare.py、tools/schedule_doubao_before.py、tests/test_doubao_compare.py。不改应用、数据库、计划签到核心或安装包；保留此前未提交的TASK-021/022资料。

## 一次性采集安排

- 已登记任务：`AIClockIn-Doubao-Before-20261115`。
- 时间：2026-11-15 00:05:00 +08:00；仅一次，不是每日签到任务。
- 当前用户 InteractiveToken、最低权限，执行 D:/Python/pythonw.exe 及项目工具的绝对路径；不启动或重启客户端，不点击领取。
- 必须保持登录、未锁屏且官方活动页已加载；截图还要求前台目标无遮挡。失去条件时记录失败/缺证据，不在稍后解锁时补采并称其为领取前。
- 输出：D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/task023/20261115/before-candidate.json 及可能的PNG。
- 这是“领取前候选采样”，电脑日期跨天不能证明活动已刷新或账号未签。当前页面可能缓存，正式前样本须检查数据后确认；不把00:05自动当作每日业务开放时间。
- 注册信息在同目录 registration.json；该任务不会唤醒本聊天自动分析，采集文件待后续读取。完成对照后应清理此唯一任务，不动 AIClockIn-Auto。

## 明日流程

1. 手动签到前先检查候选采样的 capture_ok 和 evidence_complete，并核对活动实际日期与页面新鲜度。如果采集失败，保持未签到，重新正常打开/刷新官方页面后采集新文件；不要覆盖旧证据。
2. 正常手动签到一次，成功后再采集相同官方页面。不要切换账号、重复领取或靠当天重复提交制造未签状态。
3. 自动比较前后文件；电脑日期一致、时间顺序合理、完整采样仅是比较条件，不是账号或业务状态验证。取得真实稳定标记后再整理识别模块和真实数据回归。

```powershell
# 候选失败时，手动签到前重新采集；路径示例可换为新的D盘文件。
python -B tools/doubao_compare.py capture --label before-user-claim --screenshot --out "D:\AIClockIn-probes\20261115\before.json"

# 用户手动成功后采集。
python -B tools/doubao_compare.py capture --label after-user-claim --screenshot --out "D:\AIClockIn-probes\20261115\after.json"

python -B tools/doubao_compare.py compare "D:\AIClockIn-probes\20261115\before.json" "D:\AIClockIn-probes\20261115\after.json" --out "D:\AIClockIn-probes\20261115\diff.json"
```

compare 输出路径级节点增删/变化、名称、类型、启用/焦点/屏外状态、Bounds、AutomationId、Help/ItemStatus、支持模式、脱敏页面文本和累计额变化。索引路径会受DOM重排影响，不能直接把节点差异解释成签到状态。只有语义Button且支持Invoke的“签到/立即签到”才列为候选；Group/Text即使有Invoke模式也不当按钮。候选还需唯一性、活动/账号/日期验证，工具不会调用它，也不会自动宣布已签/未签或到账。

所有输入数据只来自活动Document；URL、邀请码、手机号、JWT等做脱敏，避免读取聊天或提取会话。截图只保存可见活动横幅与Document交集，排除侧栏。GPU PrintWindow黑图会检测：仅当前台和边角均属于目标窗口时使用受限屏幕截取，否则标记截图失败。未来图片仍需人工复核脱敏，未自动上传。文件不会静默覆盖。

## 今晚真实验证

- current-a.json：真实采集238个活动节点、文本；首版截图范围不完整，正确记录未保存。
- 截图试验发现PrintWindow黑图，保留失败试验作为诊断，不当有效证据。随后修正截图回退，current-g.png已人工查看：仅公共活动横幅，无侧栏账号；不是签到成功截图。
- 脚本长命令曾触发Win32 206；改为D盘临时UTF-8 BOM脚本文件执行，使用后删除，未将其归因于客户端。
- current-g.json 与用户重开页面后的 current-h.json 是同一已手动签到阶段的真实采样；比较工具实跑0处语义字段变化，sign_state仍unknown、earned为空。此处不是未签/已签对照，不验证到账。
- D盘pythonw.exe真实运行新版采集器退出0、capture_ok/evidence_complete为true；这验证定时任务使用的解释器可运行，但明日触发尚未发生。
- 3项自动测试只验证比较器的失败保护：Group/Text不当按钮、Button不直接等同业务状态、错误日期/倒序/缺失样本拒绝。它们不是模拟签到验收。

## 标签不存在的独立测试

通过精确“关闭标签页：免费用豆包工作”关闭了活动标签，没有退出客户端；真实探针随后无活动Document、无现有标签导航目标。正常“更多”入口的Button被UIA报告为disabled；用其父级语义ExpandCollapse成功展开菜单，但现有导航器仍未取得可用活动导航项，未从缺标签状态自动恢复。该结论只证明当前路径失败，不能推断所有正常菜单入口不存在。用户随后手动重开，并完成新的真实采样。

证据：task023/cold-navigation.json、cold-more-navigation.json及前述采样。没有猜测签到坐标、模拟鼠标点击或执行领取。可靠缺标签导航仍未完成；下一阶段需要定位正确入口的可访问性路径。

## 交付状态及限制

| 目标 | 当前结论 |
| --- | --- |
| 今日已签识别 | 未完成，等待真实同日领取前后对照 |
| 今日未签识别 | 未完成，目前没有真实未签样本 |
| 唯一签到按钮 | 未完成，不将Group/Text或里程碑按钮当签到 |
| 可靠进入活动页 | 已有标签可选择；缺标签路径本轮实测失败 |
| 到账确认 | 未完成，不以累计额差值代替实际奖励 |
| 锁屏自动执行 | 不支持，保留已验证的失败/未知处理 |

下一步是在11月15日取得完整真实前样本，再配合一次用户手动签到取得后样本；尚未决定或实现自动领取。未来识别模块仅基于真实标记，自动领取仍需许可。本轮不打包、不提交/推送、不修改旧平台；没有为了造对照额外领取。

实际文件：上述3个代码文件、本说明及TASKS/HANDOFF/PROJECT/CHANGELOG增量记录。3项局部测试、真实采集/比较、pythonw执行和任务注册/NextRunTime检查，另做语法与diff检查；应用代码未改，不重复全量回归或打包。明日采集和真实签到对照保持待办，不能标完成。


### TASK-023 progress: 2026-11-15 before-sample validation

Scheduled 00:05 capture ran exit0, 238 nodes/text/banner saved, but no new-day/status or sign button evidence. One normal UIA browser Refresh (no claim) followed by fresh capture at 00:11/00:13 revealed 239 nodes and one enabled Button named 立即签到 with Invoke. Original files retained; refreshed data stored as before-recheck-001/002.json under D workspace task023/20261115. Date in page still absent; pending user same-account/today confirmation and actual manual success/post sample. Passive bounded watcher started without restore/select/scroll/claim actions to capture user transition; not yet claimed success. Added passive and button-region capture options to comparison tool; identified blank PrintWindow button crop, rejected it as visual evidence and changed screenshot path to guarded foreground-only capture (post-change visual verification pending). Banner image reviewed as public promotional area, not sign status. Three comparison guard tests and syntax check pass; no core/database/package changes. User manual action requested asynchronously; no after sample or state recognizer yet. Before assessment: task023/20261115/before-assessment.json.
