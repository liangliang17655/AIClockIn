# TASK-017：豆包工作识别复核、错误诊断和安装版交付

历史记录说明：TASK-018 已在同一 v0.5.0 路径重建发布候选，最终包、SHA256和更新检查结论以 [发布前验收](RELEASE-0.5.0-READINESS.md) 为准；下文TASK-017哈希与403状态属于此前实测。

用户确认继续实施与重新打包。范围：官方可见身份/今日状态复核，正常/最小化及可配合的关闭/锁屏读取，错误保真，v0.5.0 EXE 与 Inno Setup 构建，隔离安装/回滚/任务验证。无需重新调研入口，不领取、不切换账号，不修改原平台核心或 SQLite 语义。

## 实施步骤

1. UIA 读取官方账号管理页和活动页；稳定 ID、明确日期状态缺失时维持未知。
2. 最小改进安全错误信息与桌面可访问性检查；先测试，后实现。
3. 执行真实可达场景，并将用户未配合或环境不可达场景标记未验证。
4. 全量回归、v0.5.0 构建及离线自检；隔离安装和回滚，不碰生产账号或自动任务。
5. 检查公开 GitHub 最新 Release 的真实可用性；不存在可用版本时不编造线上更新通过。
6. 记录产物路径、哈希、修改文件、真实验收与限制。

原有未提交 TASK-014/015/016 代码与文档保留，不自动提交或发布 GitHub。

## 实际结论

- 官方“豆包账号管理”页、个人资料页可通过 UIA 访问。显示脱敏手机号、昵称以及一个“豆包号”候选标识；没有读到明确 UID/用户 ID 标签。豆包号是否可修改、切换账号后的对应关系，以及额度页属于哪个账号，均未验证。没有保存该候选标识或手机号，不以其绑定历史，仍为“账号身份待确认”。
- 尚无可靠的当前日期已签到/未签到证据。此前活动卡片的“每日签到”“+200”和累计 200 不足以判定；本版仍返回“状态未知”，没有新增自动领取或未经验证的日期判定规则。本轮主要读取账号与额度管理页，未取得新的活动页日期证据，不宣称已完成所有签到状态分支的真实验证。
- 新版代码正常读取额度页：总额 200、已用 0、剩余 200，到期文字“12月14日 19:05 到期”。最小化后重复读取相同数值，已恢复窗口。
- 用户手动锁屏约 10 秒并解锁；探针在 2026-11-14 20:15:46 +08:00 捕获输入桌面访问 Win32 5。返回查询失败、未知额度，不采用缓存，不判定登录失效。后续样本显示输入桌面恢复可访问。将真实失败结果经过生产 record 函数写入隔离 SQLite，核实 state=额度查询失败、earned=NULL、balance=NULL。
- 客户端完全退出已捕获连续真实“客户端未运行”样本，独立进程检查为0；额度和奖励为空，未误报登录失效。真实失败结果使用同一 record 函数写入隔离 SQLite 后，state=额度查询失败、earned=NULL、balance=NULL。没有自动重启客户端，测试探针已停止。

## 修改文件与原因

本轮生产改动：

- `aiclockin/doubaowork.py`：只读检查当前输入桌面，读取前后拒绝不可访问桌面，避免锁屏缓存误报；保留 UIA 异常阶段、类型、HRESULT 或子进程退出码，丢弃未经审查的原始 stderr/message，不泄露整页或凭据。
- `VERSION`：0.4.2 → 0.5.0，将上一阶段已接受的 GUI/只读模块正式打包。
- `tests/test_doubaowork.py`：先增加失败测试，再实现结构化异常和不可访问桌面保护。
- `tests/verify_install_diagnostics_windows.py`：候选版本从 VERSION 读取；基线使用已构建 v0.4.2，不再复制正式安装；新证据分版本保存。
- `tests/verify_release_task_windows.py`：当前目录版 EXE 的隔离真实计划任务执行与数据保护检查。
- `tests/verify_release_helper_windows.py`：隔离的完整运行时辅助更新、原生 Setup、自动启动和真实版本校验失败恢复；UIA 只关闭指定临时 EXE 的测试窗口。
- `README.md`、本记录及 TASKS/HANDOFF/PROJECT/CHANGELOG：更新本地交付、测试范围和后续任务。

本次安装包还包含上一阶段已确认的 `doubao_gui.py`、gui.py 只读入口、selfcheck.py 合成 GUI 行断言和相关测试。没有再次修改 WorkBuddy/Trae 核心、store 字段/加密格式、Service、Windows 任务实现、安装器或更新器逻辑；`git diff --exit-code` 对上述受保护文件通过。

## 实际验收

| 检查 | 命令/方法及实际结果 | 边界 |
| --- | --- | --- |
| 全量回归 | `python -B -m unittest discover -s tests`：91 项通过 | 协议及错误分支包含模拟；不等于真实平台签到 |
| 正常/最小化读取 | 新版 query，UIA WindowPattern Normal→Minimized→Normal，额度均为 0/200、剩余 200 | 本机本页；不是其他电脑或后台服务实测 |
| 锁屏 | 用户手动 Win+L；独立只读探针实际捕获 Win32 5；解锁后桌面恢复 | 锁屏时不支持查询，不把失败当登录失效 |
| 关闭客户端 | 用户退出后，连续真实样本返回客户端未运行，Get-Process 独立核实进程为0；同一持久化路径记录失败和 NULL | 不要求退出后可查额度；没有清除登录或自动重启 |
| 冻结 EXE / Setup 构建 | `release.ps1 -BuildPython D:/个人开发软件/AI工作区/temp/AIClockIn-build/venv/Scripts/python.exe`：PyInstaller、离线自检、Inno 均退出 0 | 未安装到生产目录；本机 Windows 11 x64 |
| 安装诊断及回滚 | `python -B tests/verify_install_diagnostics_windows.py`：基线→0.5.0 成功，1ms 超时及版本不符退出10并恢复原 EXE 哈希、数据与临时任务 XML；缺 _tkinter 依赖输出具体阶段/类型/堆栈，失败首装启动文件清理 | 使用合成数据和隔离 AppId，不代表其他实体电脑 |
| 桌面/开始菜单 | 调用上述脚本 verify_shortcuts，测试关闭改用 UIA，首装链接目标/参数正确，GUI 和本地 .runtime 启动，卸载只清理自有链接 | 临时唯一名称，不修改正式快捷方式 |
| 实际 Windows 任务 | `python -B tests/verify_release_task_windows.py`：真实注册并运行唯一临时任务，调用新版 EXE --silent，禁用合成账号时如实退出1；DPAPI/历史/设置文件哈希、任务 XML 不变；临时任务删除、正式任务不变 | 验证任务启动与数据路由，未进行真实平台领取；豆包不进入此任务 |
| 本地更新辅助程序 | `python -B tests/verify_release_helper_windows.py`：完整辅助程序等待隔离 PID，真实 Setup 安装0.5.0、自动启动 GUI，合成数据哈希不变；再用真实版本校验失败安装包测试 restored 状态和 EXE 哈希恢复 | 未验证公网下载；测试注册表使用唯一 AppId，未替换生产安装 |
| GitHub 更新检查 | 调用生产 `update.check('0.4.2')`，实际返回 HTTP403，程序给出可重试错误 | 无法确认可用正式 Release/附件，线上“检查→下载→安装”未通过；未关闭 SSL、未添加 Token |
| 打包资源 | manifest 中34个文件哈希全匹配，未含 data；PyInstaller Analysis 中包含 doubao_gui/doubaowork | EXE 需与运行时目录一起分发 |
| 文档及受保护代码 | `git diff --check`；对核心/存储/任务/安装/更新文件 `git diff --exit-code` 通过 | 没有提交或推送 |

首次构建日志用 PowerShell 5 的 `*>` 重定向时，原生 PyInstaller 的 INFO stderr 被 ErrorAction Stop 当错误。改用 Python subprocess 接收日志后重新执行构建成功；没有为此改动项目构建脚本或依赖版本。

## 产物

- `dist/release/v0.5.0/AIClockIn-v0.5.0-Setup-windows-x64.exe`：13,865,690 字节。
- 同目录 `AIClockInSetup.exe`：相同安装包；`SHA256SUMS.txt`：两种文件名的校验值。
- SHA256：`eee6c22544a7b734fc5a1999b784f7e6fff878e6d3d394722c6f1c0d863928bf`。
- 目录版：`dist/bundle/v0.5.0/AIClockIn/AIClockIn.exe`，必须保留旁边 `_runtime-v0.5.0-*` 和 manifest，不能只复制 EXE。
- 升级使用新版 Setup 沿用原安装目录，无需先卸载或清理 data。测试验证合成账号和历史不变；真实生产 data 本轮未修改。
- 本轮未上传安装包、未修改公开下载链接目标、未发布 GitHub Release。README 明确公开链接仍为0.4.2。

## 证据与仍未验证事项

证据主目录：`D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/`，含 build-release-0.5.0.log、github-update-0.5.0.json、task017-live-quota.json、task017-live-minimized.json、task017-session-probe.json、task017-lock-validation.json、task017-scheduled-0.5.0.json、task017-helper-0.5.0.json。安装证据另在 `outputs/AIClockIn-validation/install-diagnostics/v0.5.0/`。

此前其他电脑安装失败的已知路径冲突修复与原生自检诊断仍保留，新包本机安装及回滚通过；本轮没有其他电脑、Windows10实体机、Defender拦截或受控文件夹策略实测，不能宣称跨电脑兼容问题全部解决。当前锁屏结果是如实失败，不是后台读取成功。账号切换、安全身份绑定、明确今日签到证据和自动领取仍未实现；不得靠累计/卡片金额推断。

下一步：由原报错电脑运行0.5.0并查看 diagnostics；排除 GitHub403或发布者上传正式Release后再做线上更新链路；继续验证稳定账号标识和明确签到证据。均不需要泄露凭据或删除 data。关闭实测证据另见 task017-closed-probe.json、task017-closed-validation.json。
