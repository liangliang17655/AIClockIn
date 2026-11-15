# TASK-027：确认绑定、返回活动页与带日期的官方签到明细

2026-11-15，北京时间。源码阶段完成单账号确认绑定及“今日已签到”识别；完整每日自动领取仍未完成。本轮没有领取、打包、提交、推送或发布。

## 五项结论

1. **绑定与复核已实现并对当前账号真实完成。** 用户在本轮明确确认后，保存源码版data/doubao-binding.json，执行前重新读取、保存前再次确认指纹一致。模式为user_confirmed_visible_number，不冒充已验证平台UID。真实换号未实测；真实读取对照隔离错误绑定已验证会在导航前停止。
2. **身份读取后自动返回活动页已真实通过。** 修复设置对话框残留及同名活动标签处理；两次身份读取前后匹配，最终活动Document实际可读。不是仅凭Invoke返回认定导航成功。
3. **找到可靠的“今日已签到”证据。** 官方“我的奖品”→“奖励发放明细”，表格同一行：2026-11-15 00:23 / 每日签到 / +200额度。执行前后身份匹配、表头校验及同一行关联后才认定已签。不是累计值或本地历史推断。
4. **“今日未签到”仍缺证据。** 明细没有对应行可能是未加载或未展示，不能当作未签；旧唯一签到Button没有业务日期。还需带当前业务日期的明确未签状态，或经实测验证的官方当日可领取标识。未知/冲突均停止。
5. **尚不具备完整自动领取的所有必要条件。** 除上述未签证据，还需确认平台允许的领取方式、未签日一次提交及到账复核/不确定结果处理的真实整链路验证。现有生产自动任务和发布版没有被替换成每日豆包签到。

## 修复与实现

- 独立绑定文件使用现有DPAPI/原Windows用户加密，原accounts.json格式和SQLite schema不变。文件异常不覆盖，已绑定其他账号不静默替换。昵称不参与匹配。
- 新绑定入口由Tk主线程显示确认，后台读取；确认后再次读同一指纹才原子保存。用户取消不写文件。源码实际绑定经本轮用户明确确认，不把测试中的confirmed=True当作用户授权。
- 设置页对话框内没有名为“关闭”的Button，原关闭逻辑没有执行；全局“关闭”属于主窗口，不能调用。设置对话框虽然暴露WindowPattern.Close，实际返回COM 0x80040204。修复为只在已识别设置对话框获得本客户端焦点后，发送一次正常Esc并验证原RuntimeId消失；不能获取焦点就失败，不向其他程序发键、不绕锁屏。
- 奖励明细对话框的Esc没有关闭它；它有唯一真实Button，UIA ClassName明确包含closeIcon-。在已确认的奖励对话框内调用该唯一关闭Button，验证消失；不猜坐标，不把Group/Text当作签到Button。
- 重复打开菜单曾留下多个同名活动标签：优先使用唯一可见活动Document或当前唯一已选标签，其余歧义停止，不关闭用户标签。
- 官方奖励表头必须精确为“时间 / 日常任务 / 获得奖励”；按同一DataItem行解析明确日期时间、每日签到和正额度。滚动完成、弹窗及表格加载均有截止时间。重复当日记录、字段改变、未关闭弹窗或与可领取Button冲突均保留未知。
- 新独立流程：加载确认绑定→检测桌面/正常启动（复用）→实时身份匹配→活动页→官方奖励明细→再次身份匹配→返回活动页→再次检查桌面→保存。只有前后匹配且返回成功才关联绑定ID，否则按次独立记录。
- 新状态是“今日已签到（查询，未领取）”。SQLite earned/balance仍为NULL，官方过去的200额度放在detail.official_receipt，避免冒充本次新增领取。没有新增领取入口、请求或点击。

## 真实证据

默认根目录：`D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/task027/`。

|文件|真实结果|
|---|---|
|consumption-detail.json|实际打开消耗明细，读到日期但无签到/奖励流水，不作签到证据|
|identity-close-fixed.json|连续两次相同可见账号指纹，settings_closed=true|
|binding-save-result.json|用户确认后保存并重载成功；原账号文件与历史DB哈希不变|
|bound-flow-report.json|早期同名标签歧义导致失败，原样保留|
|bound-flow-fixed-report.json|身份前后匹配并返回活动页，但当时还没有明细读取，正确unknown|
|current-bound-page.json|真实有效活动页完整采样；正文无业务日期|
|reward-ledger-structure.json|官方奖励表头及同一行父节点关联：11-15 00:23/每日签到/200；另有11-14记录|
|ledger-reader-result.json|早期关闭失败，dialog_closed=false，不赋予已签状态|
|ledger-reader-fixed-result.json|真实明细解析成功、弹窗关闭成功|
|bound-ledger-flow-report.json|早期滚动/加载时序导致未取到明细，正确unknown|
|bound-ledger-wait-fixed-report.json|完整前后身份复核，official_time=2026-11-15 00:23，official_reward=200，already_signed，claim_attempted=false|
|bound-minimized-report.json|先最小化真实客户端，新绑定流程恢复窗口并得到相同已签结果，退出0|
|mismatch-f44f1e2df9e9/result.json|真实当前身份对照故意错误的隔离测试绑定，account_mismatch、导航0次、原文件不变；不是实际切换真实账号|

源代码临时Windows任务实测：`task025/6683529d215d/result.json`（既有测试脚本沿用task025输出目录）。当前用户InteractiveToken运行Python绝对路径及源码绝对路径，使用已确认源码数据目录；已签查询退出0、未领取，临时任务清理成功，生产任务XML前后相同。AIClockIn进程数量检查为0。不能把这项源码测试说成新版EXE/安装版测试。

本轮不需要再领取一次验证今天的已签状态，也没有用前一天样本替代当前明细。

## 文件与验证

新增：aiclockin/doubao_binding.py、aiclockin/doubao_receipt.py、tests/test_doubao_binding.py、tests/test_doubao_binding_gui.py、tests/test_doubao_receipt.py、tests/verify_doubao_binding_windows.py、本计划和结果文档。

修改：aiclockin/doubao_session.py、aiclockin/doubao_session.ps1、aiclockin/doubao_gui.py、main.py、.gitignore、tests/verify_doubao_prepare_windows.py（可指定已确认数据目录）、README及项目记录。其他既有未提交修改保留。

- 测试驱动：绑定、日期明细分类、冲突状态及末尾锁屏停止先失败再实现通过。
- 全量 `D:\Python\python.exe -B -m unittest discover -s tests -p 'test_*.py'`：最终133项通过。曾发现未绑定GUI文案回归并修复；受控单元测试不当成真实平台领取。
- GUI最小570x580布局及取消确认无写入，均通过。
- PS Parser.ParseInput UTF8源码：0语法错误；git diff --check通过。
- git diff确认providers/auth/service/store/schedule核心无修改，原账号/旧历史不清除、无schema迁移，生产任务不改。data与独立绑定文件均被Git忽略。

## 使用与未验证项

源码窗口内“绑定当前账号…”需要确认；“核对账号并检查签到状态”执行上述流程。独立入口仍为`main.py --doubao-prepare --data <确认绑定所在D盘目录> --report <D盘报告>`；未绑定即停止。今日已签可退出0，表示查询/跳过完成，不表示本次领取成功；未知/身份不符退出非0。

未验证：真实切换其他账号、新绑定流程从完全退出客户端开始的整链路、跨天未签识别、允许的自动领取及其回查、其他电脑、新版EXE/安装包。锁屏不支持执行；本轮增加末尾锁屏停止受控测试，未重复要求用户锁屏实测。正式发布版仍是v0.5.0，不包含本轮源码功能。
