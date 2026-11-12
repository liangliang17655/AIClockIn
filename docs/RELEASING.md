# v0.4.0 起的打包与发布

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

不要上传源码 ZIP 作为更新包。代码推送不等于发布 Release。README 的 raw-main 固定下载入口需要另外上传根目录同名 Setup；未上传之前不能宣称链接可用。本任务未创建 Release 或推送二进制。

## 更新机制

启动后台/手动检查 GitHub 最新正式 Release，显示 Release 正文。HTTPS 下载、进度、超时重试与 SHA256 校验后，复制完整当前运行目录到 D 盘独立辅助目录。辅助进程等待旧进程退出，按原程序和数据绝对路径静默运行 Setup，再离线健康检查并重启；失败恢复原启动文件、元数据及卸载登记，旧依赖仍在。安装期间互斥阻止该安装的其他实例启动，不强杀签到操作。更新目录不放 data。

v0.3.x 旧更新器不认识 Setup，必须手动运行一次新安装包。新版正常启动不再显示自制 Tk 安装器。旧项目根 EXE 保留原样，不能用文件夹版单个 EXE 覆盖它。

## 数据与验证

Setup 不覆盖账号、SQLite、历史、更新偏好；卸载保留数据，自动任务仅在路径、数据参数、当前用户都匹配时移除。升级保留 EXE 路径，所以原计划任务继续有效。凭据仍由原 Windows 用户 DPAPI 解密。

实际测试与未验证边界见 [TASK-008 验收](INNO-PLAN.md)。发布前运行必要回归及真实隔离安装/升级/卸载测试。当前没有可信代码签名，SmartScreen 提示可能继续出现，换成 Setup 不会消除它。Inno 启动器使用 Windows TEMP；构建和应用更新暂存显式使用 D 盘。
