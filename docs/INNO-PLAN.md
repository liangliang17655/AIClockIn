# TASK-008 · PyInstaller 文件夹版 + Inno Setup

2026-11-12。用户明确批准改为真正 Setup 两步流水线，并要求标准向导、目录选择、桌面/开始菜单、卸载。基线 9843ae8，接入工作区干净；分支 feature/inno-setup。

## 已确定的方案

- PyInstaller 继续 6.22.3，使用 --onedir，依赖放版本化 `_runtime-v版本号`。Inno Setup 7.1.1 x64 打包整个输出，依赖先复制、主 EXE 最后复制；旧依赖保留以便失败恢复，不用一个 EXE 覆盖文件夹版。
- 固定 AppId、当前用户安装（PrivilegesRequired=lowest），默认 D:/AIClockIn，保留目录选择。旧安装优先沿用原目录和 --data；不复制/覆盖/删除 data，不更改登录状态。桌面/开始菜单/卸载由 Inno 原生管理。
- 去掉首次启动的 Tk 自制安装器；正常程序直接进入主界面，保留设置中的补建桌面入口。增加进程存活互斥，安装/卸载要求关闭当前安装的 GUI/worker，不强杀签到进程。
- 更新源改为正式 Release 中版本化 Setup EXE，保持 HTTPS/SHA256；由 D 盘独立的完整运行目录副本等待旧进程退出后启动 Inno，同路径安装，离线健康检查后重启。不能再只复制一个文件；失败恢复旧 EXE、元数据和仍保留的旧依赖。
- 新用户下载 AIClockInSetup.exe；0.3.x 的旧更新器只认识便携 EXE，首次切换须手动运行新版 Setup，不伪称旧客户端已经支持新格式。
- Inno Setup 是构建工具，不改变 Python/Tk 签到框架，也不解决未签名的 SmartScreen 信誉提示。不会购买证书、关闭防护或自动发布 Release。

## 安装工具/临时文件

官方 https://jrsoftware.org/isdl.php 当前推荐 7.1.1；已从官方链接下载，Authenticode=Valid，发布者 Pyrsys B.V.，SHA256 8a5a6711c3766a6e5fb74f280ba0e3551e719ce94538d901fdbd1f8f9920b3f0。工具使用官方 /PORTABLE=1 /CURRENTUSER，放 D:/个人开发软件/AI工作区/temp/AIClockIn-tools/，下载缓存在同工作区 cache/installers。构建/测试/应用更新明确设置 D 盘 TEMP。Inno 启动器遵循 Windows 的系统 TEMP；本机当前为 D:/个人开发软件/DevTools/temp，其他机器依其 Windows 设置，不声称原生 Setup 在所有电脑都只能用 D 盘临时目录，不修改系统环境变量。

## 实施与验收步骤

1. 先写失败测试，验证 Setup 命名选择、完整目录备份、互斥、数据保护、原数据参数、安装脚本不包含 data/数据库删除。
2. 修改 build/release，增加 installer/AIClockIn.iss、编译工具引导脚本及构建文件清单；版本 0.4.0。
3. 改入口/更新适配，保留原签到模块；安装包支持旧目录的本地静默配置探测与数据路径参数，测试无需真实凭据。
4. 编译真实 Setup，验证向导、D 盘目录检查、桌面和开始菜单链接、卸载登记、首装/覆盖升级/静默运行/卸载保留合成 DPAPI 配置与 SQLite/历史，以及临时计划任务同路径可运行；不改用户生产任务。
5. 运行必要回归和独立审查；只对修改导致的新问题补测，不重复安装依赖。更新 README/发布规范/任务/变更/交接；未执行的线上、SmartScreen签名及硬件故障场景明确标注。

当前：已完成本地实现和隔离验证，详见下方实际结果。


## TASK-008 实际交付与验证（2026-11-12）

目标：以原生 Inno Setup 替代首次运行的 Tk 安装入口，保留签到核心和数据。v0.4.0 本地实现完成，未提交/推送、未发布正式 Release、未安装到用户生产目录。

实际修改：VERSION、build.ps1、release.ps1、main.py、aiclockin/{package,setup_support,setup_update,update,update_apply,update_gui}.py、installer/AIClockIn.iss、tools/bootstrap-inno.ps1；测试 test_setup_package/test_setup_update/test_update_gui、verify_inno_windows/verify_setup_helper_windows/preview_inno；README、AGENTS、PROJECT、TASKS、RELEASING、INNO-PLAN、CHANGELOG、HANDOFF。根目录新增 AIClockInSetup.exe 作为本地交付，不替换旧 AIClockIn.exe。原因：文件夹版升级必须管理完整依赖、原生快捷方式与卸载登记，不能仅覆盖单 EXE。

实际验证：

- `python -B -m unittest discover -s tests -q`：72 项通过。
- `release.ps1 -BuildPython <已有D盘Python>`：PyInstaller 文件夹构建、自检及 Inno 编译通过；ISS 局部修改后以 `-Bundle .\dist\bundle\v0.4.0\AIClockIn` 复用已验证目录重新编译通过。
- `python -B tests/verify_inno_windows.py --reuse-bundle`：真实隔离首装、桌面/开始菜单及卸载登记、运行中拒绝覆盖且不强杀、强制健康检查失败恢复、0.4.0→0.4.1升级、同版重装、合成 DPAPI/SQLite/历史和偏好不变、唯一临时任务 XML 不变且可执行、卸载保留数据并移除链接/登记、临时任务清理通过。生产任务未改动。
- `python -B tests/verify_setup_helper_windows.py`：完整运行目录辅助进程实际调用原生 Setup、0.4.1 健康检查、自动启动新 GUI、合成数据不变、原生安装失败恢复通过。
- `python -B tests/preview_inno.py`：捕获并检查真实中文欢迎页，安装前退出。逐页鼠标交互自动化未通过，未将其标记为完成；目录参数/安装目录和链接由上述真实静默安装验证。
- 独立审查发现关闭更新弹窗引用未定义变量，先补失败回归再修复。安装全程共享互斥；运行依赖采用每次构建唯一目录并不覆盖已有依赖，保留失败恢复条件。
- `git diff --check`：通过。签到核心 providers/auth/workbuddy_auth/store/service/schedule 未改；原根 EXE 保持原样。

产物：根 AIClockInSetup.exe 与 dist/release/v0.4.0/ 同名和版本化安装包，13,848,776 字节；SHA256 `0a6ddb2a7cbeb5c7d6c8bc6adb2c9f35ca309d0b0d00e4d821d490e5d08e7343`。校验清单在发布目录 SHA256SUMS.txt。验证证据在 D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/inno/，含 inno-windows.json、setup-helper.json、日志和 setup-welcome.bmp。

未验证/风险：真实 GitHub Release 在线下载升级未验证（未发布新版）；用户生产账号未执行签到，生产安装未迁移；原生逐页点击、真实生产名任务卸载和实体断电/杀毒隔离未测试。当前未签名，SmartScreen 信誉提示不保证消失。Inno 启动器遵循系统 TEMP；本机 D 盘，不保证其他机器固定 D。旧版本依赖为恢复保留，会增加安装目录占用。v0.3.x 首次迁移须手动运行 Setup，保留原目录和数据。

下一步：用户可先运行本地 Setup 验收向导和桌面入口；确认交付后按 RELEASING 发布正式附件。README raw 下载链接要上传同名文件后才生效，不宣称线上已更新。
