# TASK-016：豆包工作只读接入实施与验收

用户已确认直接实施。使用 writing-plans 技能记录最小计划；在当前目录保留原有未提交研究文档，不自动提交。

## 设计

Python 标准库调用系统 Windows PowerShell 的 UIAutomationClient，Raw View 有界遍历，通过精确 Document 标题限定额度页与活动页。仅提取额度字段，不输出整页，不调用 Invoke/Expand/Scroll，不访问凭据。读取限时，失败不复用旧值，不判定签到成功。

首版只关联“当前客户端只读会话”，账号身份待确认；不改 accounts.json 格式、不把会话加入 Service 或计划任务。每次查询用新 UUID，SQLite 原表保存额度查询结果；earned 保持空，balance 仅活动赠送剩余，其余字段放结构化 detail。历史显示平台查询记录而非同账号历史。

## 文件与步骤

- [x] 新增 tests/test_doubaowork.py：先验证来源冲突、未知字段、持久化、超时、敏感输出抑制。
- [x] 新增 aiclockin/doubaowork.py：内嵌系统 UIA 只读探针、校验与记录，不增加依赖或资源打包规则。
- [x] 新增 aiclockin/doubao_gui.py：简洁额度面板、关联/刷新、未知标记；平台按次历史使用原列表，只在主线程更新控件。
- [x] 修改 aiclockin/gui.py：加入只读会话入口、平台名称和历史显示，保护原有操作。
- [x] 本机真实读取、GUI 与最小化测试；关闭/超时/缺字段用模拟验证错误处理，严格区别实测；不主动关闭登录客户端、锁屏或注册真实任务。
- [x] 现有平台回归、文档与截图；不重新发布安装包，不修改核心/安装/更新。

## 未实测环境

锁屏、注销、无人值守计划任务、客户端关闭与跨版本稳定性不承诺支持。缺失稳定账号 ID 与明确今日状态时保持未知，不启用多账号或自动领取。

## 实际实现与文件

- 新增：aiclockin/doubaowork.py、aiclockin/doubao_gui.py、tests/test_doubaowork.py、本实施记录。
- 修改：aiclockin/gui.py、tests/test_gui.py、README.md、aiclockin/selfcheck.py，以及 TASKS/HANDOFF/PROJECT/CHANGELOG。自检仅调整合成 GUI 账号集合断言以包含新增只读行，不移除安装验证，不启动 UIA。
- store.py、service.py、providers.py、auth.py、数据库结构、accounts.json 格式、任务、安装器与更新逻辑均未修改。UIA 不启动任何客户端或调用业务 API。
- 每次读取清空旧值、在后台线程运行受限 PowerShell，20 秒超时；子进程错误只输出固定安全提示，不持久化 stderr、Cookie 或整页文字。关闭额度窗口前等待正在进行的读取完成。
- 累计与额度来自不同页面，缺失身份时不在一条结果中合并；如果两类来源同时存在，本次仅采用额度页。字段缺失不使用上次结果回填，查询失败也单独记录，余额为空。
- 这里只读取页面当前展示内容，不刷新服务器；“读取时间”不是业务到账时间。记录中的到期时间保留页面原文，不猜测年份。

## 实际测试结果

| 环境 / 检查 | 实际结果及边界 |
| --- | --- |
| 新增模块真实活动页读取 | 累计 200，其余缺失字段为空；非模拟 |
| 新增模块真实额度页读取 | 总额 200、已用 0、剩余 200，到期“12月14日 19:05 到期”；非模拟 |
| 官方客户端最小化 | UIA WindowPattern 确认 Normal→Minimized，新增模块仍读到上述额度，随后恢复 Normal；仅本机本页一次实测 |
| GUI 真实查询及持久化 | 隔离 data 中进行活动与额度查询，重新打开 Store 后可读 3 条独立记录；未知身份/签到/earned 均不伪造 |
| 客户端关闭 | 不关闭当前已登录客户端；仅模拟 running=false，返回失败和空值；不宣称真实支持 |
| Windows 锁屏 | 未实测，不主动锁定用户电脑 |
| Windows 计划任务静默 | 未注册或调用真实任务；首版不接入调度，不宣称支持 |
| 慢页面 / 超时 | 缺字段及 TimeoutExpired 模拟通过，真实慢页面未制造；不宣称后台稳定性 |
| 结构变化 / 窗口冲突 | 无字段、非法数值、不完整树、冲突来源、非 JSON 和错误输出模拟测试通过；真实改版未实测 |
| 自动测试 | `python -B -m unittest discover -s tests`：89 项通过，包含 WorkBuddy/Trae 原有协议及 GUI/自检回归；没有执行真实旧平台签到 |
| 局部收尾 | 主标题计数文案调整后 `python -B -m unittest tests.test_gui`：1 项通过；`git diff --check` 通过 |

首次测试因新增模块不存在而失败后实现；首轮 GUI/自检断言仍假设一行而失败，随后更新为原合成账号加只读行的明确断言，回归通过。模拟不等同真实签到。没有执行领取、清除登录、安装、卸载或修改真实任务。

## 实际截图与证据

工作区 `D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/`：

- task016-gui-campaign.png：新增 GUI 实际累计查询。
- task016-gui-quota-cropped.png：新增 GUI 实际额度查询，裁去 PrintWindow 输出的空白边缘。
- task016-live-quota.json、task016-live-minimized.json：新模块正常/最小化实测字段。
- task016-gui-live.json：实际界面显示与重开 Store 的记录数。
- preview-task016.py 与 task016-preview-data：隔离预览及真实查询记录；不属于生产 data，不打包、不上传。

## 审查、风险与下一步

按 code-review-and-quality 做正确性、隐私、架构与异常处理自审：未更改原签到分派，虚拟会话不能进入原账号启停/删除或任务；SQLite 原表插入，无迁移，查询不会改写账号文件（测试比对原加密字节）。无新依赖，PowerShell 读取脚本内嵌以避免资源漏打包。

当前缺失稳定 UID 与明确当前日期签到标记，不能多账号查询或自动领取；昵称不能补足身份。UIA 渲染结果和标题可能随版本变化，缺字段时返回未知。后续优先验证账号标识、明确签到证据和锁屏/调度适用性。本轮只交付源码功能，安装包/EXE 构建与其他电脑实测未执行，未提交或推送。
