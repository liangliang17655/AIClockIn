# TASK-030：AIClockIn v0.5.1 本地安装包验收

2026-11-15。本轮回到正式产品：保留WorkBuddy/Trae CN，隐藏豆包入口并保留源码/旧记录，停止研究。本机Windows11 x64验证完成；其他实体电脑仍未实测。未提交/推送/发布GitHub，也未覆盖用户当前安装。

## 安装包

- `dist/release/v0.5.1/AIClockIn-v0.5.1-Setup-windows-x64.exe`
- 固定名称别名：同目录`AIClockInSetup.exe`
- 大小：13,874,856字节。
- 最终SHA256：`03378a93bf31c7819cfaf8a6c073ce4b67a5e904c9d13b8b222680aec1661351`；同目录SHA256SUMS.txt覆盖两个名称。
- 完整目录版位于`dist/bundle/v0.5.1/AIClockIn/`，其中EXE不可脱离运行时单独分发。Setup单文件已包含运行依赖。
- 初次候选因更新根目录兼容性问题被替换；上述最终包及哈希才是交付物，不混用第一次构建的哈希。

## 403具体原因与真实修复

本轮同机匿名实测：GitHub Releases API返回403，`X-RateLimit-Remaining=0`；同仓库官方`releases/latest`和`releases.atom`均200，latest重定向至正式v0.5.0。根因是共享网络出口的匿名API配额耗尽，不是安装损坏。

更新器优先API，明确RateLimited时才用同仓库官方latest正式标签、匹配Atom发布说明、指定标签SHA256SUMS和实际安装包大小建立后备更新信息。拒绝其他仓库/预发布标签、缺校验、无效大小；所有HTTPS和重定向主机白名单、SHA256、下载边界保留，无个人Token、代理轮换或关闭TLS。后备也失败仍报限流，不冒充最新。权限拒绝/无Release/网络错误分类保留，启动检查在线程中且不会导致安装回滚。

真实生产`check('0.4.2')`在此次限流条件下发现v0.5.0并读取发布说明，下载安装包13,869,293字节，SHA256匹配公开正式包；`check('0.5.1')`正确无更高版本。证据：D工作区`outputs/AIClockIn-validation/stable-0.5.1/public-update.json`、`public-download/`。

下载缓存改为应用D盘.runtime/updates。原生更新辅助实测发现，旧版辅助程序严格验证既定事务根目录，将事务一起迁移会拒绝启动。已改为**下载缓存和事务分离**，事务沿用旧D盘协议；重新构建后旧版→新版辅助安装、自动重启及失败恢复全部通过。没有迁移账号和历史。

## 安装问题的实际边界

此前已确认的跨机缺陷是安装器用Windows TEMP下的health.json，而EXE拒绝非D盘报告；开发机TEMP在D盘掩盖问题。现有修复已包含在本包：离线报告和自检工作目录位于安装目录diagnostics独立会话，不依赖开发者临时目录，不联网、不读取真实账号。保留90秒超时、进程退出码、详细异常和旧文件回滚。

本轮隐藏入口后同步修正冻结自检的GUI断言，避免把“虚拟豆包行已移除”误判为安装失败；提示明确为“安装后的离线启动验证失败”，包含原因和日志，避免与GitHub更新检查混淆。没有删除自检或绕过Defender。

**此前失败电脑没有实际日志可供本轮复核，不能声称所有异机失败原因均已排除。** 其他电脑、Windows10实机、受控目录和安全软件策略待按INSTALL-ACCEPTANCE-0.5.1.md验收。

## 实际测试

|命令/项目|结果及口径|
|---|---|
|`D:\Python\python.exe -B -m unittest discover -s tests -p 'test_*.py'`|最终145通过；含后备更新、权限/断网、SHA256校验、隐藏入口和旧记录、离线自检及原平台协议受控回归|
|`release.ps1 -BuildPython <已有D盘打包Python>`|PyInstaller6.22.3/Python3.14.7目录版、冻结离线自检和Inno Setup7.1.1构建通过，复用依赖未新装框架|
|`tests/verify_install_diagnostics_windows.py`|真旧版覆盖；超时及版本不符exit10、旧EXE恢复、合成账号/数据库/任务不变；成功自检报告在D盘；故意缺_tkinter.pyd准确保留异常阶段和traceback|
|`tests/verify_release_helper_windows.py`|完整独立辅助程序→原生Setup→新GUI自动重启通过；失败恢复通过；两个平台合成账号、历史、更新偏好哈希和DPAPI可解密性保留|
|`tests/verify_install_diagnostics_windows.py --shortcuts-only`|首装桌面/开始菜单链接及data参数正确，GUI正常启动、runtime本地创建，卸载清理自己的链接|
|`tests/verify_release_task_windows.py`|当前EXE在真实临时Windows任务运行；禁用合成账号退出1如实表示无可签账号，数据/XML不变，临时任务清理，生产任务不变|
|冻结归档/清单审计|两个原平台模块存在；豆包研究模块未打入PYZ，源码仍在；清单哈希有效、无data/账号/数据库/绑定文件|

首轮辅助测试失败已保留在native-helper.log，兼容修复后的最终证据为`stable-0.5.1/*-final.log`。其他证据：`install-diagnostics/v0.5.1/results.json`、`shortcuts.json`；既有验证脚本沿用输出名`doubaowork/task017-helper-0.5.1.json`和`task017-scheduled-0.5.1.json`，这些是正式版安装/任务回归，不是恢复豆包研究。

真实在线下载验证针对已公开v0.5.0；辅助更新验证使用本地已校验v0.5.1包。v0.5.1尚未发布，**未验证公网旧版→v0.5.1全链路**。本轮没有重复执行真实账号的签到领取，不把模拟接口或禁用账号任务退出当作真实领取成功。

## 文件、保护和使用

新增features.py、test_update_fallback.py及本轮计划/验收/发布说明/跨机清单；修改gui.py、selfcheck.py、main.py、update.py、update_gui.py、build.ps1、installer/AIClockIn.iss、VERSION、test_gui.py、test_update.py及README和项目记录。旧未提交修改原样保留，豆包源码不删。providers/auth/service/store/schedule核心无diff；不迁移或删除账号、配置、旧历史和绑定文件。

关闭当前AIClockIn后运行最终Setup，沿用原目录，勾选桌面快捷方式；不要先卸载或删data。确认界面账号与记录保留，开启自动签到后GUI关闭仍由原Windows用户的任务运行。Trae CN的9095仍是设备受限，不保证同设备所有账号可领取。

公开GitHub下载链接当前仍是v0.5.0，本轮只交付本地包。未来发布时上传版本安装包、固定别名、SHA256SUMS、RELEASE-NOTES及INSTALLATION，核实后才更新在线版本说明；本轮没有自动发布。
