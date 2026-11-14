# TASK-018：v0.5.0 发布前稳定性与安全检查

用户授权：修复更新检查错误分类，验证本机安装/更新，准备发布资料；优先开发分支提交，不自动发布 Release。分支 develop/v0.5.0-release-validation，保留先前未提交的豆包只读实现。

计划：真实采样 HTTP 状态和限流头→先测试后修复分类→配额重置后实测→重建同版本候选包→隔离覆盖安装/回滚/快捷方式/辅助更新/任务回归→源码/历史/产物敏感信息检查→跨电脑清单、更新日志与安装限制→开发分支本地提交。其他电脑和线上未发生的发布流程不标通过。

首次证据：2026-11-14 20:33:59 +08:00，latest 和仓库 API 均 HTTP403，X-RateLimit-Limit=60、Remaining=0、Resource=core；body 明确 API rate limit exceeded。/rate_limit HTTP200 同样确认 used=60。代理来自系统 urllib 配置，不记录代理凭据或公开出口 IP；原始脱敏诊断放 D 工作区 outputs/AIClockIn-validation/release-0.5.0/。服务器给出的 reset=20:36:40 +08:00。不改变代理或客户端身份来逃避限流。

参考：[GitHub 限流说明](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)、[最新 Release API](https://docs.github.com/en/rest/releases/releases#get-the-latest-release)。匿名配额按出口 IP 共享；无法仅凭代理启用就断言某个人或本应用耗尽配额。

## 根因与修复结果

- 原 API 地址正确，User-Agent/Accept 已存在，HTTPS 与证书验证开启。限流是 GitHub 对当前网络出口的匿名配额限制，不是安装包损坏。不能保证所有网络今后不再403。
- 补充固定 API 版本请求头；读取有限长度的错误响应作分类，不显示响应正文、出口IP或代理凭据。
- 403/429 有限流证据时返回 RateLimited 和可用重置时间，不立即自动重试；401/无明确限流证据的403返回访问拒绝，提示检查代理/权限，不谎称已确定是某种权限故障。
- latest404 时再核实仓库公开可访问，确认后才提示 NoRelease；仓库不可见不误报“已是最新版本”。网络/服务端失败保留有限重试，“已是最新版本”只由成功的正式版本比较产生。
- 手动无Release为信息提示，限流为等待提示；启动检查失败保持静默，不阻塞GUI/签到/离线安装验证。
- 20:37:47 +08:00 配额重置后，生产 check 返回 NoRelease。后续直接核对 latest404、仓库200/private=false，remaining49/48；确认当前无公开可用的 latest 正式 Release，非程序损坏。没有使用个人Token、代理轮换、关闭SSL或改系统代理。

## 验证结果

| 项目 | 实际结果 | 尚未验证的范围 |
| --- | --- | --- |
| 自动回归 | `python -B -m unittest discover -s tests`：95项通过；含限流、权限、网络、无Release、最新版本及GUI静默处理 | 分类分支包含模拟，不冒充公网状态 |
| GitHub实际请求 | 真实403限流→配额重置→latest404 + repo200；新提示正确 | 目前无Release，尚不能验证真实线上版本提示/附件下载 |
| EXE/Setup | 最终 release.ps1 构建成功，冻结离线自检通过，PyInstaller Analysis含豆包两个模块 | 冻结GUI主窗口实际启动通过；豆包面板入口以源码GUI测试验证，未对最终冻结GUI手动点击刷新 |
| 隔离覆盖安装/回滚 | 当前包重新运行 tests/verify_install_diagnostics_windows.py：成功安装、超时/版本不符旧EXE哈希恢复、数据/临时任务不变、缺依赖诊断保留 | 同一台Windows11 x64，非其他电脑 |
| 两平台账号保护 | 强化 tests/verify_release_helper_windows.py：禁用的WorkBuddy与Trae合成账号、各自历史和更新偏好，旧版→新版→失败恢复后账号可解密且数据哈希不变 | 未对用户真实生产安装执行覆盖，不测试真实领取 |
| 更新辅助程序 | 真实完整运行时 helper→Setup→新GUI自动重启→版本校验失败恢复，通过 | 本地已校验候选包，不是网络下载全链路 |
| 桌面/开始菜单/卸载 | 新候选包首装链接目标及data参数正确，GUI/runtime启动、卸载清理自身链接，通过 | 唯一测试名称/目录/注册表；正式用户桌面未改 |
| 计划任务 | tests/verify_release_task_windows.py真实执行当前EXE --silent；禁用合成账号时退出1，无真实请求，数据和任务XML不变，清理唯一任务 | 豆包UIA仍不加入任务，无真实旧平台领取 |
| 受保护核心 | providers/service/store/auth/workbuddy_auth/schedule/installer 无新增差异 | 更新检查模块是本轮批准修改项 |

豆包功能范围不变：身份待确认、今日状态未知、每次独立记录；正常/最小化真实额度、用户协作锁屏和退出时失败/NULL证据沿用TASK-017，因为本轮未改豆包读取实现，不重复打扰用户。锁屏失败不是后台查询成功。

## 安全检查

检查当前源码、全部可达历史blob、远程地址是否带凭据、禁止的账号/数据库文件名、构建清单与内容哈希。首次审计扫描90个当前路径、175个历史blob、34个运行时文件：无账号/数据库/.env路径、无GitHub令牌或私钥命中、远程地址无内嵌凭据、bundle无data。后续文档增量在提交前再扫描。

唯一数值模式命中位于Python `unicodedata.pyd`二进制；与D:/Python/DLLs同名原始运行时SHA一致，人工认定为数字字节串误报，不是个人手机号。涉及Token/Cookie字段的生产源码复核为运行时读取/请求构造，selfcheck仅synthetic-secret，没有硬编码个人凭据。模式扫描有覆盖边界，不作为所有秘密绝对不存在的数学证明。证据与原始网络诊断留在D工作区，不上传Git。

本轮不把旧根目录AIClockInSetup.exe当作新包，不改公开旧下载入口为不存在的新URL。新产物只从dist/release/v0.5.0取得，源码提交不带data或运行日志。

## 最终候选产物

- `dist/release/v0.5.0/AIClockIn-v0.5.0-Setup-windows-x64.exe`：13,869,293字节。
- `AIClockInSetup.exe`：相同内容别名；`SHA256SUMS.txt`覆盖两个名称。
- 最终SHA256：`2b8f6ab38b506acd584fcf73edc178ce5fbff7150de9238ef06bbb2a8317695a`。替代TASK-017旧候选hash，不混用校验文件。
- `RELEASE-NOTES.md`（来源docs/releases/v0.5.0.md）、`INSTALLATION.md`（来源跨电脑清单）。
- `dist/bundle/v0.5.0/AIClockIn/AIClockIn.exe`为目录版，须连同运行时分发。

## 修改文件、发布步骤与剩余门槛

本轮改动：aiclockin/update.py、update_gui.py、tests/test_update.py、test_update_gui.py、verify_release_helper_windows.py；README、docs/RELEASING.md、本报告、跨电脑清单、docs/releases/v0.5.0.md与TASKS/HANDOFF/PROJECT/CHANGELOG。开发分支提交同时包含此前用户已接受但未提交的豆包模块、GUI/自检断言与研究/验收文档；不静默覆盖原改动，不上传产物或私人数据。

发布步骤见RELEASING.md顶端v0.5.0流程：确认开发分支→合并main→标签v0.5.0→按更新日志准备正式Release和正确附件→用户批准后发布→旧版真实联网更新验收。当前仅本地开发分支提交，不合并main、不推送、不打标签、不创建或发布Release。

其他电脑首次/覆盖/卸载/失败诊断清单见INSTALL-ACCEPTANCE-0.5.0.md。仍未验证：Windows10实体机、其他实体电脑、Defender/受控目录策略、正式Release的公网下载与更新全链路、最终冻结GUI里的豆包刷新。此前异机自检路径修复保留且新候选本机回归通过；不能据此宣称异机兼容全部解决。

证据：D工作区outputs/AIClockIn-validation/release-0.5.0/（HTTP根因/恢复、构建、安全审计），install-diagnostics/v0.5.0/（最终安装/快捷方式），doubaowork/task017-helper-0.5.0.json、task017-scheduled-0.5.0.json（最终包重新验证，文件名沿用但以本次时间和内容为准）。下一步优先执行其他电脑清单，批准正式发布后再验证线上链路。
