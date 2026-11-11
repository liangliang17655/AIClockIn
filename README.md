# AIClockIn

## 下载使用（无需拉取代码）

**[点击下载最新 Windows 版本](https://github.com/liangliang17655/AIClockIn/releases/latest)**

进入发布页面，在 **Assets** 中下载 `AIClockIn-v版本号-windows-x64.exe`。将下载文件放到固定的 D 盘目录，重命名为 `AIClockIn.exe`，双击运行即可，无需安装 Python 或下载源码。

首次发布前，下载页面可能显示 404，表示正式版尚未发布。请勿将 GitHub 自动生成的 Source code ZIP 当作安装包。

已有用户请保留原目录中的 `data` 文件夹；该文件夹保存账号和签到记录。从 v0.2.0 起，可通过右上角“设置 → 检查更新”升级；v0.1.0 需要先关闭软件并手动替换一次 EXE。

一个独立、简单的 Windows 本地签到工具。只做 WorkBuddy / Trae CN 多账号签到、结果记录和后台定时。

**v0.2.0 · 2026-11-11**。Python 标准库 + Tkinter，独立应用代码；必要的 WorkBuddy 本机登录适配按 MIT 署名复用，见 [来源与许可](THIRD-PARTY-NOTICES.md)。不是将旧签到脚本整体换一层界面。

软件启动后会在后台检查最新正式 Release；网络异常不影响原有功能。手动检查、自动检查开关和版本信息位于右上角“设置”。更新包通过 SHA256 校验后才允许安装；详情及维护者打包发布步骤见 [发布与更新说明](docs/RELEASING.md)。

## 使用

双击本目录的 `AIClockIn.exe`，无需另外安装 Python。

1. WorkBuddy：先在官方桌面端登录，再点“添加 WorkBuddy”；切换其他账号后再次添加。已添加的账号会保留，WorkDaddy 保存的账号也会被发现。
2. Trae CN：先安装并登录官方桌面客户端，点击“添加 Trae CN”，在浏览器完成授权；不同账号分别授权添加。不生成用来绕过领取限制的设备身份。
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

账号和历史只存在本项目的数据目录。更新只替换 EXE，保留 `data`。移动 EXE 后重新点击开启自动签到，更新任务路径。密文一般只能由原 Windows 用户/机器解密，不要复制后期待其他用户可用，也不要把明文凭据提交到 GitHub。

所有应用新增数据及临时文件在 D 盘，EXE 固定解压至 `D:/个人开发软件/AI工作区/temp/AIClockIn/runtime`。D 盘不可用会停止，不自动回退 C 盘。

## 开发与验证

```powershell
python -B main.py
python -B -m unittest discover -s tests -v
.\build.ps1
```

应用运行只需标准库。打包使用 PyInstaller 6.22.3，依赖、缓存和构建目录在 D 盘。可通过 `build.ps1 -BuildPython <Python绝对路径>` 复用已有打包环境；默认找不到打包依赖时建立 D 盘隔离环境。脚本仅复制 EXE，不覆盖 data。

离线自检：`AIClockIn.exe --self-test --report D:/AIClockIn-selftest.json`，使用临时合成数据，验证加密、历史、GUI 和打包，不请求真实平台。`tests/verify_windows.py` 只创建唯一名称的临时空账号任务，验证静默执行和数据目录，然后清理。

新项目真实账号授权和签到是否通过，以 [交接](docs/HANDOFF.md) 的实际记录为准；模拟通过不代表真实接口可用或所有账号均有奖励资格。

## Git

本目录是独立 Git 仓库，默认分支 `main`，公开仓库为 [liangliang17655/AIClockIn](https://github.com/liangliang17655/AIClockIn)。自动更新功能在 `feature/github-updater` 分支开发；代码提交与正式 Release 分开管理，下载安装包需按 [发布步骤](docs/RELEASING.md) 上传正式附件。

`.gitignore` 排除账号、数据、日志、构建产物和新增 EXE；已被 Git 跟踪的根目录 EXE 不会因此自动取消跟踪，本次未擅自移除。源码、测试、图标、文档和许可可进入仓库。正式分发使用 GitHub Releases，保留 MIT 和来源声明。

需求、架构和决策见 [项目文档](docs/PROJECT.md)，开发进度见 [任务](docs/TASKS.md)。
