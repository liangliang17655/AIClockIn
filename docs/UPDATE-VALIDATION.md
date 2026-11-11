# TASK-002 · v0.2.0 自动更新验证

2026-11-11，用户确认方案后实施。验收依靠受控接口、合成账号与隔离 Windows EXE，未使用真实平台账号领取积分。没有自动提交、推送、打标签或发布 GitHub Release。

## 修改文件

- `aiclockin/update.py`、`version.py`：固定公开仓库最新正式 Release、数字版本比较、附件选择、HTTPS/重定向限制、流式下载、重试/取消、SHA256/大小/x64 校验。
- `aiclockin/update_gui.py`、`gui.py`：右上角设置、手动/启动检查、自动检查偏好、关于、远程说明、进度、安装确认。更新事件独立于签到事件，不能意外清除签到忙碌状态；更新窗口最小尺寸下按钮仍可见。
- `aiclockin/update_apply.py`、`health_process.py`、`main.py`：本地辅助进程、退出等待/互斥、同目录暂存、强制落盘备份、写穿替换、隔离合成数据健康检查、恢复/重启、中断恢复。自检进程启动前加入 Windows Job，超时清理全部后代；不终止用户签到进程。
- `VERSION`：0.2.0；`build.ps1`：修复缺少 PyInstaller 时检测命令被 PowerShell 提前终止；`release.ps1`：本地构建/自检、版本化 EXE 和 SHA256SUMS，不执行远程发布。
- `tests/test_update*.py`：23 项新增测试；`verify_update_windows.py`、`verify_health_timeout.py`、`fixtures/update_hang.py`、`preview_update.py`：可显式运行的隔离验证。
- `README.md`：下载安装入口及更新使用方式；`.gitignore`：新增 EXE 忽略（不移除已跟踪文件）；`docs/RELEASING.md`、`UPDATE-DESIGN.md`、`UPDATE-PROGRESS.md`、`PROJECT.md`、`TASKS.md`、`HANDOFF.md`、根目录 `CHANGELOG.md`：发布规范、批准决策、执行和验收记录。
- 项目根 `AIClockIn.exe`：验证完成后按本地替换事务部署新版，结果见交接；不是从源码 ZIP 更新。

## 实际执行

| 命令/检查 | 结果 |
|---|---|
| `python -B -m unittest discover -s tests -v` | 43 项全部通过，原 20 项及新增 23 项；经历测试失败后实现及修复 |
| `release.ps1 -BuildPython D:/个人开发软件/AI工作区/temp/DailyCheckin-build/venv/Scripts/python.exe` | 复用已有 PyInstaller 6.22.3，构建成功；EXE 离线 DPAPI/历史/Tk 自检及包内版本 0.2.0 验证通过 |
| `python -B tests/verify_update_windows.py` | 新辅助 EXE 驱动隔离 0.1.0→0.2.0 副本替换、健康检查及自动 GUI 重启；合成多账号密文/数据库/偏好/任务备份文件哈希保持一致，DPAPI 解密不变 |
| 同上，独立 `AIClockIn-UpdateTest-<随机>` 任务 | 升级前后 XML 完全相同；升级后原绝对路径和自定义带空格 `--data` 能运行新版；禁用合成账号退出码 1，如实报告无启用账号，无网络签到；临时任务移除核验通过 |
| 同上，故意错误的期待版本 | 真实新 EXE 自检版本不符，恢复旧哈希；不是只 mock 文件替换 |
| `python -B tests/verify_health_timeout.py` | 使用专用单文件卡死测试 EXE，启动嵌套单文件子进程；5 秒自检超时后完整 Job 退出，恢复目标成功，子进程退出核验通过 |
| `python -B tests/preview_update.py` | 合成界面与更新弹窗截图，默认/紧凑主界面和弹窗已检查；最小弹窗按钮可见性另有自动测试 |
| GitHub 匿名实际请求 | 方案阶段 latest=404、Release/tag 列表为空；实施末期实际检查得到 HTTP 403，按失败提示，未绕过限制或配置 Token |
| `git diff --check`、核心哈希、文档链接/忽略规则 | 收尾核对，详见交接；原 providers/auth/workbuddy_auth/store/service/schedule 不变 |

43 项回归覆盖：两个平台核心原行为；账户加密/独立/历史；原调度；数字版本/不降级/非法标签/非正式拒绝；附件去重/指定仓库；SHA256 缺失、重复、冲突和篡改；截断/取消/进度；离线重试/404；GUI 启动回调、手动反馈/重试、远程文本、偏好持久化、忙碌状态；替换/恢复/占用/恢复失败/互斥/备份刷盘/进程树超时。

## 用户 12 项验收对应

| 项 | 结果与证据边界 |
|---|---|
| 1 低版本检测 | 受控 Release 数据通过，含 0.1.9/0.1.10 数字比较；线上更高正式版未验证 |
| 2 已最新提示 | GUI 与版本测试通过，启动静默、手动提示 |
| 3 启动自动检查 | Tk 延迟回调/后台线程实现和测试通过；EXE 正常启动；真实联网目前 403 |
| 4 手动检查 | 菜单/结果/失败后允许重试测试通过 |
| 5 Release 说明 | 受控远程 body 展示和截图通过；真实 Release 说明因未发布尚未验证 |
| 6 正确下载附件 | 筛选/HTTPS边界/流式受控响应通过，正式发布附件已打包；实际 GitHub 附件下载未验证 |
| 7 下载进度 | 受控流式响应和 GUI 进度事件通过；截图不是联网下载证明 |
| 8 包完整性 | SHA256/大小/PE 检查与失败用例通过，打包校验文件已生成 |
| 9 安装/重启 | 隔离真实 Windows 辅助程序、替换、健康检查、重启通过；旧 v0.1.0 自身不支持启动更新，首次引导仍需手动换 EXE |
| 10 数据保留 | 合成 DPAPI 多账号/数据库/历史/设置哈希与解密通过；不进行数据迁移或刷新登录态 |
| 11 任务正常 | 唯一临时任务升级前后 XML/路径/参数和升级后真实触发通过；未触发用户生产任务 |
| 12 网络失败不影响 | 受控失败重试与 GUI/原核心回归通过；未物理断开主机网络 |

## 审查与未验证项

一次独立审查无 Critical，发现两项 Important：冻结自检超时遗留内层进程、备份未强制刷盘。已补先失败后通过测试，改为创建后暂停、加入 Job 后再运行，以及 fsync 备份/暂存、MoveFileExW WRITE_THROUGH；43 项全量回归、真实嵌套冻结超时及真实升级流程通过。没有派发二次审查。截图检查另修复说明区挤掉按钮的问题。

未验证：GitHub 正式 Release 发布后真实互联网端到端升级、实体断电、磁盘故障/防病毒强制隔离恢复、多个真实 Windows 用户交互、真实平台账号领取。断电顺序已加强但未物理断电验收，不能承诺所有硬件故障均可恢复。备份保留在 D 盘事务目录；恢复失败明确报错。

正式发布附件为 `dist/release/v0.2.0/AIClockIn-v0.2.0-windows-x64.exe` 和 `SHA256SUMS.txt`。最终 EXE SHA256：`9badc04a53c48b8c0445b99c6402aba5d3ba9283bfeda22845156008038aca9b`。具体发布步骤见 [RELEASING.md](RELEASING.md)。
