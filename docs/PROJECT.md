# AIClockIn

## 需求与验收（用户已确认）

2026-11-11，独立新项目。用户希望只保留核心签到功能，全新页面，本地 Git 仓库，日后自行上传 GitHub；保留后台自动签到。

- 支持 WorkBuddy / Trae CN 多账号添加、重命名、启停、删除。
- 一个“立即签到”依次执行所有启用账号；一个失败继续下一个，已签不重复领，领取后回查。
- 展示简单持久记录：时间、账号、结果、当次获得、余额、失败原因。未知值不填 0。
- 主界面明确自动签到是否启用，关闭窗口不影响后台任务；Windows 当前用户登录状态下独立运行 EXE --silent。
- 不保留推送、手动快照入口、设备模拟、旧命令集合及复杂报表。
- 账号在本项目 data 内加密保存，不读写旧软件账户；更新保留 data。不能保证平台不允许的账号均能领取。

## 架构

- aiclockin/models.py：结构化签到结果。
- aiclockin/http.py、providers.py：本项目独立 HTTP 和两个平台核心流程，接口事实参照已验证实现，不导入旧项目模块。
- aiclockin/auth.py：Trae 浏览器授权、本机登录读取；workbuddy_auth.py 仅承载署名的 MIT 本机登录适配。
- aiclockin/store.py：DPAPI 账号、SQLite 历史、跨进程互斥。
- aiclockin/service.py：逐账号执行、凭据更新、脱敏后的记录。
- aiclockin/schedule.py：一个独立 AIClockIn-Auto 任务，包含每日、登录及恢复触发。
- aiclockin/gui.py：全新简洁窗口；独立 worker 处理网络，界面只读结果。
- main.py：GUI / --silent / 账号授权 / 自动设置 / 离线自检入口。
- build.ps1：D 盘隔离构建并打包单文件 EXE。

## 决策

- TASK-006：仅优化设置菜单，保持现有主界面布局和浅色配色；SettingsMenu 管理弹层，UpdateUI 使用事件队列回传快捷方式结果，不再为补入口拉起安装器。用户下载版的蓝色提示已确认是 SmartScreen；没有可信证书，不自动解除下载标记、关闭防护或伪造发布者，不将 GUI 修复等同于数字签名。

- TASK-005，2026-11-11 用户确认：增加安装入口和桌面快捷方式。复用同一单文件的 installer.py，不引入安装框架；新用户默认 D:/AIClockIn，已有用户保留当前 EXE/data/任务路径，不迁移账号。桌面 .lnk 按 Windows 当前用户实际桌面位置写入（用户明确授权桌面入口，可能在 C 盘，仅写快捷方式）。详见 [安装方案与验证](INSTALL-PLAN.md)。
- 首次无本地数据且无显式 --data 的冻结 GUI 显示安装窗口，在创建 Store 前完成路由；后台任务、自检和更新辅助不进入安装。设置菜单支持为原目录补快捷方式。链接目标和 --data 使用绝对路径；不同目标同名链接拒绝覆盖。

- TASK-002，2026-11-11 用户确认：增加 GitHub 正式 Release 自动更新，继续便携单文件形式，使用本地 EXE 副本作为独立辅助程序，仅替换原绝对路径的 EXE；不迁移 data，不重建计划任务。详见 [技术方案](UPDATE-DESIGN.md)、[发布说明](RELEASING.md) 和 [验证记录](UPDATE-VALIDATION.md)。
- 更新模块：update.py 负责 Release/HTTPS/校验；update_gui.py 负责菜单和异步交互；update_apply.py 负责互斥、替换、恢复和重启；health_process.py 用 Windows Job 隔离新版自检进程树；version.py 读取包内 VERSION。main.py 在访问真实数据前协调更新。检查只在 GUI 启动，不在静默签到和健康检查中运行。

- 已批准：Python + Tkinter，保留后台定时功能。
- 实现选择：单个 Windows 任务减少管理复杂度；固定每日六次并补登录/恢复，界面不提供复杂定时表达式。
- 实现选择：默认不注册系统任务，首次界面清楚显示“未开启”；由用户显式点击开启，不干扰旧软件。
- 实现选择：独立数据、独立任务；旧账户与任务不自动迁移。
- 实现选择：应用自主编写；有限 MIT 登录适配如实保留来源和许可，不声称严格 clean-room。
- 授权仅限正常平台流程；Trae 实际设备标识取本机客户端，不生成领取用的替代设备身份。

未验证：真实接口在新项目中的当前可用性、用户是否需要后续迁移旧账号。未做任何数据迁移。
