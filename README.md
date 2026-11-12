# AIClockIn

## 下载软件

**[点击下载 AIClockIn 自动签到 Windows版本安装包](https://raw.githubusercontent.com/liangliang17655/AIClockIn/main/AIClockInSetup.exe)**

下载的是带安装向导的 `AIClockInSetup.exe`，无需拉取代码或安装 Python。

适用于 Windows 64 位系统，提供 WorkBuddy 多账号管理与依次签到，以及 Trae CN 签到功能。

**Trae CN 的同设备多账号领取限制尚未解决。** 软件可以保存多个 Trae CN 账号，但不代表这些账号都能在同一台电脑上领取奖励。遇到 `9095` 会记录为“设备受限”，不能宣称支持同设备多账号全部签到成功。

下载 `AIClockInSetup.exe` 后双击，按原生安装向导选择目录和桌面快捷方式。默认安装到 `D:\AIClockIn`，以后双击桌面的 **AIClockIn 自动签到** 即可打开，无需安装 Python。

已有账号的用户会保留原程序和数据目录。想补回桌面图标时，在软件右上角点击 **设置 → 创建桌面快捷方式**。

首次运行如果出现蓝色的“Windows 已保护你的电脑”，当前版本会显示“发布者未知”（尚未进行可信数字签名）。请先确认文件来自本仓库；确认后在该提示中点击 **更多信息 → 仍要运行**，才会进入安装窗口。无需关闭 Windows 安全防护。该提示发生在软件启动之前，代码更新不代表提示一定消失。[微软关于 SmartScreen 的说明](https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation)

已有用户请保留原目录中的 `data` 文件夹；该文件夹保存账号和签到记录。v0.3.x 及更早版本首次升级到 v0.4.0，需要关闭软件后手动运行新版 Setup，沿用原安装目录；后续新版发布到 GitHub 正式 Release 后，可通过“设置 → 检查更新”安装；仅推送代码不会触发软件更新。

一个独立、简单的 Windows 本地签到工具，提供账号管理、签到执行、结果记录和后台定时。Trae CN 的实际领取受设备限制，具体以平台返回结果为准。

**v0.4.0 · 2026-11-12**。Python 标准库 + Tkinter，独立应用代码；必要的 WorkBuddy 本机登录适配按 MIT 署名复用，见 [来源与许可](THIRD-PARTY-NOTICES.md)。不是将旧签到脚本整体换一层界面。

软件启动后会在后台检查最新正式 Release；网络异常不影响原有功能。手动检查、自动检查开关和版本信息位于右上角“设置”。更新包通过 SHA256 校验后才允许安装；详情及维护者打包发布步骤见 [发布与更新说明](docs/RELEASING.md)。

## 使用

首次安装完成后，双击桌面上的 **AIClockIn 自动签到**，无需进入安装目录寻找 EXE。

1. WorkBuddy：先在官方桌面端登录，再点“添加 WorkBuddy”；切换其他账号后再次添加。已添加的账号会保留，WorkDaddy 保存的账号也会被发现。
2. Trae CN：先安装并登录官方桌面客户端，点击“添加 Trae CN”，在浏览器完成授权。可以保存不同账号的授权，但同设备多账号领取限制尚未解决；不能保证每天所有账号都领到奖励。受限时如实记录，不生成替代设备身份。
3. 点击“全部签到”，依次处理所有启用账号。已签到的跳过，一个失败继续下一个。选择账号可以查询状态、重命名、停用或删除。
4. 点击“开启自动签到”，顶部实际状态变为“已开启”后，就不需要每天手动打开窗口。

主界面没有“快照导入”、推送渠道或复杂报表。记录中的“—”表示未知，失败不伪装成功。Trae 返回 9095 会标记“设备受限”，不会改设备或反复领取。

## 自动签到怎么运行

开启后由 Windows 任务 `AIClockIn-Auto` 直接执行 EXE 的绝对路径，参数为 `--silent --data <本项目数据目录>`；无需界面、外置 Python 或 BAT/VBS。

- 每日 08:45、11:45、14:45、17:45、20:45、23:45。
- 进入当前用户的 Windows 桌面后延迟补跑，睡眠恢复后补跑。
- 关闭软件窗口不影响已启动操作或后续自动任务。
- 电脑关机、睡眠、注销时不能执行；重新进入可运行状态后由 Windows 补跑。需要正常网络和有效凭据。
- 日常锁屏不等于注销。上限一小时，重叠任务忽略；应用另有操作锁保护。

**默认未开启自动任务。** 这是全新应用，不会自动导入旧软件账号，也不会停用或删除旧软件的任务。切换使用时，请在旧软件里停用它的自动签到，避免两套软件同时请求同一账号。

## 数据与更新

```text
AIClockIn/
├── AIClockIn.exe
├── _runtime-v0.4.0-…/     # 必须保留的运行依赖
├── install-info.ini       # 安装时记录数据路径
├── main.py
├── aiclockin/              # 独立应用源码
├── assets/app.ico
├── tests/
├── docs/
└── data/                  # 运行后生成，Git 忽略
    ├── accounts.json      # 当前 Windows 用户 DPAPI 加密
    ├── history.db         # 不含凭据的历史记录
    └── task-backup.json   # 自动设置变更前备份
```

账号和历史只存在本项目的数据目录。更新由 Inno Setup 替换程序及完整运行依赖，保留 `data` 和原路径，计划任务继续使用同一 EXE。文件夹版不能单独移动 EXE。卸载会移除程序和快捷方式，保留账号、历史和自动设置；只清理属于当前安装的自动任务。密文一般只能由原 Windows 用户/机器解密，不要复制后期待其他用户可用，也不要把明文凭据提交到 GitHub。

应用改为 PyInstaller 文件夹版，启动无需单文件临时解压。程序、数据、应用更新暂存放 D 盘。Inno 原生启动器使用 Windows TEMP（本机已在 D 盘，其他电脑取决于系统设置）；桌面、开始菜单及卸载登记遵循当前 Windows 用户路径。

## 开发与验证

```powershell
python -B main.py
python -B -m unittest discover -s tests -v
.\release.ps1
```

应用运行只需标准库。打包使用 PyInstaller 6.22.3，依赖、缓存和构建目录在 D 盘。可通过 `build.ps1 -BuildPython <Python绝对路径>` 复用已有打包环境；默认找不到打包依赖时建立 D 盘隔离环境。先由 build.ps1 生成完整文件夹，再由 release.ps1 调用 Inno Setup；安装包不包含 data。

离线自检：`AIClockIn.exe --self-test --report D:/AIClockIn-selftest.json`，使用临时合成数据，验证加密、历史、GUI 和打包，不请求真实平台。`tests/verify_windows.py` 只创建唯一名称的临时空账号任务，验证静默执行和数据目录，然后清理。

新项目真实账号授权和签到是否通过，以 [交接](docs/HANDOFF.md) 的实际记录为准；模拟通过不代表真实接口可用或所有账号均有奖励资格。

## Git

本目录是独立 Git 仓库，默认分支 `main`，公开仓库为 [liangliang17655/AIClockIn](https://github.com/liangliang17655/AIClockIn)。代码提交与正式 Release 分开管理，下载安装包需按 [发布步骤](docs/RELEASING.md) 上传正式附件。

`.gitignore` 排除账号、数据、日志、构建产物和新增 EXE；根目录旧 AIClockIn.exe 保留原样，不是新版文件夹版的分发入口。源码、测试、图标、文档和许可可进入仓库。正式分发使用 GitHub Releases，保留 MIT 和来源声明。

需求、架构和决策见 [项目文档](docs/PROJECT.md)，开发进度见 [任务](docs/TASKS.md)。
