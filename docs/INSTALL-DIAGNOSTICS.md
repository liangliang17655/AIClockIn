# TASK-013 · 2026-11-14 · 异机安装自检失败

已确认缺陷：installer/AIClockIn.iss 的 ssPostInstall 以 {tmp}/health.json 调用 EXE --self-test；main.py 在 selftest 之前拒绝非D盘 --report。开发机 Windows TEMP在D盘掩盖该错误；其他机器TEMP在C盘时，即使安装在D盘也会触发。已用 main.main + C盘报告参数重现 ValueError（未向C盘写文件）。尚未取得报错机器日志，不把此机制推断为每台报错机唯一根因。

其他代码证据：Exec ewWaitUntilTerminated 无自定义超时；非零退出、缺失报告、版本不符或路径登记失败都被同一except通用提示覆盖；selftest发生在现有异常报告捕获之前。selftest使用合成DPAPI/SQLite/Tk且禁用更新检查，没有GitHub依赖，但仍异步读取本机任务。PyInstaller为onedir，不临时解压；固定D盘开发目录及权限是另一风险。未见Defender隔离证据，不归因杀软。

实施范围（用户已要求修复并重新打包）：
1. 先加失败回归：Python自检异常/prepare失败必须报告具体阶段和traceback；自检不触发网络/计划任务；报告仍限定D盘。
2. 自检隔离模块；安装报告及工作目录放安装目录diagnostics独立会话，避开系统TEMP和开发者固定路径；只用合成数据。记录版本、Python/Windows、位数、阶段、异常、路径，不读取账号或打印凭据。
3. Inno保留验证：90秒进程级等待，自检失败保留退出码/异常/报告路径；启动失败/缺失报告/版本不符分别记录。当前窗口失败退出10、原程序恢复和数据/任务保护不变。
4. 版本0.4.2，重建完整运行目录和Setup；局部回归→全量→隔离原生安装/失败恢复/数据保持；仅在D盘测试。不声称已在其他实体电脑或Defender隔离条件下验证。对方复测获取diagnostics日志，不需要GitHub网络。

不改WorkBuddy/Trae协议、账号格式、数据库或计划任务策略。工作区原TASK-012三份未提交记录保留。实际结果收尾增量记录。


## 已确认的调用链与根因证据

旧版调用链：Inno ssPostInstall → Exec(AIClockIn.exe --self-test --report {tmp}/health.json) → main.main解析参数 → prepare → 非D盘report被ValueError拒绝 → __main__以1退出（带--参数不弹异常）→ Inno Code非0 → except覆盖具体异常 → 通用“新版本检查失败”。

在修改前用原main.main、C:/Users/Other/AppData/Local/Temp/health.json参数重现“报告只能写入D盘”，未向C盘写文件。开发机TEMP在D盘，所以以往本地安装通过没有覆盖这一场景。其他电脑有D盘不代表Windows TEMP在D盘。此为已证实的程序缺陷；尚未取得报错实体电脑日志，不能断言是其唯一原因。

另一确证缺陷：第一次安装验证失败时，旧DeinitializeSetup只处理HadExe=True，可能留下失败程序；因此“报失败但目录有EXE”不代表安装完整。现在HadExe=False仅移除本次新建启动文件，不递归清目录；有原程序时恢复备份。不会删除data/账号/历史。

## 实现结果

- main.py 将自检提前交给aiclockin/selfcheck.py，异常覆盖prepare/imports/dpapi/sqlite/tk各阶段。报告含版本、Windows/Python/位数、阶段、异常类型/信息/traceback；仅合成数据，无真实凭据。
- installer/AIClockIn.iss 保留启动、退出码、成功标志和版本验证。报告在安装目录 diagnostics/install-会话/health.json；自检临时目录在同会话work，避免系统TEMP和固定开发者目录。诊断install.log保存实际异常和退出码。SetupLogging启用，原生安装日志按Windows TEMP（本机D，异机可能C，属已说明的原生Setup临时行为），弹窗也显示该日志位置。
- 用Win64 CreateProcessW直接启动自检，不使用PowerShell/WSH、下载脚本或联网。90秒超时，只终止本次自检进程，最多再等3秒并核对状态，finally关闭进程/线程句柄后恢复旧EXE。首次WSH实验曾导致恢复Win32=32共享冲突，已用原生进程句柄管理替代并实际验证旧4.1文件哈希恢复。恢复失败本身也独立记录，不宣称恢复成功。
- 自检禁用UpdateUI自动检查和计划任务查询；不读真实Store目录、不运行任何平台签到。frozen正常运行的临时目录也改到程序旁.runtime，开发源码运行仍使用D工作区。更新事务缓存沿用既有方案，本任务未扩展改写。
- 构建仍为PyInstaller6.22.3/Python3.14.7 Windows x64 onedir，Tcl/Tk/SQLite依赖随完整目录打包；不进行单文件临时解压，不要求对方安装Python。本运行时支持Windows10及更新版本，见[Python官方说明](https://docs.python.org/3.14/using/windows.html)。未降级Python或声称支持Windows7/8。
- 没有修改providers/auth/workbuddy_auth/service/store/schedule，未迁移真实账号/数据库、未修改生产计划任务。

## 实际验证

| 验证 | 结果/边界 |
|---|---|
| python -B -m unittest discover -s tests -q | 78项通过；新增异常阶段、prepare权限失败、无网络/无任务查询、C环境TEMP但D工作目录、自检报告D约束、安装版临时路径回归 |
| build.ps1 -BuildPython 已有D盘Python | 完整目录重新构建成功；未重复安装依赖 |
| release.ps1 -Bundle dist/bundle/v0.4.2/AIClockIn | 自检/版本/真实Inno编译exit0；最终SHA见下方 |
| python -B tests/verify_install_diagnostics_windows.py | 真正旧4.1→候选4.2超时/版本不符时，旧EXE哈希恢复；合成DPAPI/SQLite/历史不变、唯一临时任务XML不变；成功安装报告落D；故意移除_tkinter.pyd准确保留imports异常及traceback，首次失败启动文件被清理 |
| python -B tests/verify_install_diagnostics_windows.py --shortcuts-only | 新目录首装桌面/开始菜单链接存在，目标和--data参数正确；正常GUI启动且.runtime落在安装目录；卸载清理自有链接 |
| git diff --check | 通过；核心文件无差异 |
| 独立审查 | 发现超时后的终止状态需检查，已修复；原生Win64布局与句柄清理复核无阻塞项 |

本机实际安装测试在Windows11 x64；未做其他实体电脑、Windows10实体机、真实C盘TEMP原生Setup启动、Defender隔离或受控文件夹策略实测。C盘TEMP场景为代码逻辑复现与环境变量回归，不伪装成其他电脑验收。权限失败单元测试为模拟异常，未擅自修改本机真实目录ACL。未进行真实签到、未发布正式GitHub Release。没有关闭Defender或跳过证书/安装验证。

证据：D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/install-diagnostics/ 的 results.json、shortcuts.json、missing-dependency-health.json、diagnostic-*.log、build-0.4.2.log、release-0.4.2.log。

## 对方电脑的本地复测方式

1. 下载v0.4.2，关闭当前程序后运行Setup，沿用原目录。需要桌面入口时勾选“创建桌面快捷方式”。无需先卸载，不关闭Windows防护。
2. 失败时按弹窗打开安装目录 diagnostics/install-会话/install.log 与 health.json；两份文件重装失败后保留。若程序没进入Python报告可能不存在，此时提供install.log的启动错误/退出码、原生Setup日志或系统原始DLL提示；不能仅凭无报告判为Defender。
3. 可选显式安装日志：AIClockInSetup.exe /LOG="D:\AIClockIn-setup.log"。或直接在安装目录运行 .\AIClockIn.exe --self-test --report "D:\AIClockIn-diagnostics\health.json"，无需GitHub网络。
4. 若日志指向权限/依赖或启动被拦截，再核对相同时间的Windows安全中心保护历史和安装目录权限；没有记录就不认定是Defender。提供Windows版本/位数、安装路径和上述诊断即可，不需要accounts.json、真实凭据或数据库。

后续：等待报错电脑使用新包复测；没有其日志前，不能把本机通过写成所有电脑已修复。

最终v0.4.2 Setup：13,855,332字节，SHA256 `65da9bdae4c7dca82b186e37942f4567147567ec3bd2c46f3985c237da7b4ae0`。两个发布文件和SHA256SUMS位于dist/release/v0.4.2。
