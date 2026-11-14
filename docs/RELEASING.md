# v0.4.0 起的打包与发布

## v0.5.0 发布流程

TASK-020：用户另行授权后已正式发布 v0.5.0；发布标签指向 31735cc，安装包与校验文件已上传。公开 API 检查、更新说明、公网下载和SHA256验证通过；真实用户机器上的完整安装升级等待本地反馈。此前“不执行发布”的限制已由本次明确授权覆盖。

1. 在开发分支检查差异、测试、敏感信息扫描与安装产物。合并 main 前核对本机验收和跨电脑未验证项，确认发布条件；不要把“本机通过”写成全环境通过。
2. 将经过确认的开发分支合并 main 后，核对 VERSION=0.5.0、源码提交和安装包的对应关系，再创建指向该提交的 v0.5.0 标签。不要在未确认的提交上先打标签或发布。
3. 打开仓库 Releases → Draft a new release，选择 v0.5.0，标题“AIClockIn v0.5.0”，正文使用 docs/releases/v0.5.0.md。
4. 从 dist/release/v0.5.0 上传 AIClockIn-v0.5.0-Setup-windows-x64.exe、SHA256SUMS.txt；可附相同内容的 AIClockInSetup.exe 固定别名和 INSTALLATION.md。不要上传 data、数据库、账号、日志、源码 ZIP 或整个 dist。
5. 核对附件 SHA256、大小、标签和正文，确认用户批准发布后才点击 Publish release；正式发布不勾选 Pre-release，检查其被设置为 Latest。
6. 发布后再将 README 下载地址改为 `https://github.com/liangliang17655/AIClockIn/releases/latest/download/AIClockInSetup.exe`，必须先确认固定别名附件真实存在。当前 README 的旧下载地址不冒充新版本。
7. 用发布前旧版进行真实检查→说明→HTTPS下载→SHA256→辅助安装→重启验收，再记录公网完整链路结果。无 Release 时应显示未发布，不是已是最新。不得为解决限流把个人 Token 放入客户端。

发布状态与真实证据见 [v0.5.0 发布准备](RELEASE-0.5.0-READINESS.md)，其他电脑清单见 [安装验收](INSTALL-ACCEPTANCE-0.5.0.md)。下方旧版“提交根目录安装包并用 raw 下载”的说明为历史工作方式，v0.5.0 正式发布优先使用 Releases 附件。

用户批准 PyInstaller 文件夹版 + Inno Setup 原生安装包。应用仍为 Python/Tkinter；Setup 当前用户安装，默认 D:\AIClockIn，提供目录选择、桌面/开始菜单与卸载。已有安装沿用原路径，数据不迁移。

## 构建

在 Windows x64 项目根目录执行：

```powershell
.\tools\bootstrap-inno.ps1
.\release.ps1 -BuildPython <已有打包Python的绝对路径>
```

工具引导固定 Inno Setup 7.1.1 官方下载的 SHA256 和签名发布者，工具及缓存放 D 盘。不配置 GitHub Token，不关闭 TLS 校验。build.ps1 使用 PyInstaller 6.22.3 --onedir，生成 dist/bundle/v版本/AIClockIn；release.ps1 执行离线自检后调用 ISCC。仅修改安装脚本时可用 -Bundle 指定已验证目录复用构建。

完整依赖使用每次构建唯一的 _runtime-v版本-标识，升级保留旧依赖用于恢复；不要只分发其中的 AIClockIn.exe，也不要手动删除仍用于恢复的旧依赖。data 从不进入安装包。

## 正式 Release

修改 VERSION，提交源码，创建对应 vX.Y.Z 标签；Release 不选 Draft/Pre-release。标题用版本号与简短主题，正文列实际修复/新增/已知限制。从 dist/release/vX.Y.Z 上传：

- AIClockIn-vX.Y.Z-Setup-windows-x64.exe（更新器识别的正式安装包）
- AIClockInSetup.exe（相同文件的固定名称，方便直接下载）
- SHA256SUMS.txt（同时包含上述两个名称）

不要上传源码 ZIP 作为更新包。代码推送不等于发布 Release。README 下载入口使用已上传安装包的完整提交 SHA 地址，避免 main 文件缓存返回旧版本。每次发布新版安装包并推送后，核对该提交下文件 SHA256，再更新 README 下载地址与版本号并推送；不能只更新本地安装包。v0.4.1 已上传根目录 Setup，但尚未创建正式 Release。

## 更新机制

启动后台/手动检查 GitHub 最新正式 Release，显示 Release 正文。HTTPS 下载、进度、超时重试与 SHA256 校验后，复制完整当前运行目录到 D 盘独立辅助目录。辅助进程等待旧进程退出，按原程序和数据绝对路径静默运行 Setup，再离线健康检查并重启；失败恢复原启动文件、元数据及卸载登记，旧依赖仍在。安装期间互斥阻止该安装的其他实例启动，不强杀签到操作。更新目录不放 data。

v0.3.x 旧更新器不认识 Setup，必须手动运行一次新安装包。新版正常启动不再显示自制 Tk 安装器。旧项目根 EXE 保留原样，不能用文件夹版单个 EXE 覆盖它。

## 数据与验证

Setup 不覆盖账号、SQLite、历史、更新偏好；卸载保留数据，自动任务仅在路径、数据参数、当前用户都匹配时移除。升级保留 EXE 路径，所以原计划任务继续有效。凭据仍由原 Windows 用户 DPAPI 解密。

实际测试与未验证边界见 [TASK-008 验收](INNO-PLAN.md)。发布前运行必要回归及真实隔离安装/升级/卸载测试。当前没有可信代码签名，SmartScreen 提示可能继续出现，换成 Setup 不会消除它。Inno 启动器使用 Windows TEMP；构建和应用更新暂存显式使用 D 盘。


v0.4.1 安装成功且健康检查通过后，在当前用户 HKCU/Software/应用AppId 的 DataDirectory 中保留数据路径（不含凭据）。卸载不删除该位置记录；换目录重装时验证 D 盘旧账号/历史文件存在后复用，显式 /DATA 参数优先。不扫描全盘、不迁移文件。此记录仅同一 Windows 用户有效；原 data 被手动删除不属于可恢复情况。


v0.4.2 起安装自检报告与work放安装目录diagnostics会话目录；正常运行缓存为程序旁.runtime。保留90秒验证、真实退出码、版本核对和失败恢复。跨电脑故障分析、复测命令及实际验证边界见 [安装诊断](INSTALL-DIAGNOSTICS.md)。发布时必须区分本机回归与其他电脑实测。
