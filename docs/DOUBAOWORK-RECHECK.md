# TASK-014：升级后复核（2026-11-14）

后续 TASK-015 已通过独立 Windows UIA 读取真实活动和额度页；下文连接阻塞属于当时状态。当前证据与剩余限制见 [UIA 排查报告](DOUBAOWORK-UIA-DIAGNOSTICS.md)。

本节更新此前调研的当前状态，不以旧版客户端的读取结果推断新版。

## 已确认与未验证

- 用户确认已升级至 2.36.15_win_34505、个人账号登录、找到活动入口并手动签到成功。入口阻塞已解除；这不是 AIClockIn 自动查询验证。
- 本机读取实际 app/manifest.json：2.36.15、release。Get-CimInstance 确认官方 app/DoubaoWork.exe 正在运行。构建后缀 34505 未独立验证。
- 界面连接返回 apps=[]、browsers=[]、browser access host is unavailable，无法读取活动页。新版业务控件可读性尚未验证。
- 官方 API 总览与文档索引未找到个人签到/奖励余额能力；不能据此断言所有接口不存在。
- getAccountInfo/getAccountInfoSync 返回应用插件信息（appId/envVersion/version），支持表标注 PC 不支持，不是个人账号识别接口。
- Firecrawl CLI 不存在，未安装新工具；采用网页工具及匿名 HTTPS 读取公开文档。

## 结论及下一步

没有取得机器可核验的账号、今日状态、实际奖励或剩余额度样本，数据仍未知，暂不满足平台接入条件。本轮没有添加空界面、账号识别、查询、入库或领取功能；没有读取 Cookie、清除登录、修改旧平台核心、数据库、计划任务、安装或更新机制，没有重新打包。

下一步需要恢复可用的客户端界面读取连接后验证活动页字段，或取得官方明确支持的个人只读查询/导出。无需再次要求用户升级、登录、寻找入口或手动签到。恢复连接本身不代表查询能力已验证。

## 实际验证与范围

manifest 和进程只读检查通过；公开文档复核完成；界面连接失败。没有进行真实业务查询、签到、SQL 集成或模拟测试。仅维护研究及任务交接文档，不运行无关全量回归或构建。文档检查使用 git diff --check；没有提交或推送。

实际修改文件：本文件、docs/DOUBAOWORK-FEASIBILITY.md、docs/TASKS.md、docs/HANDOFF.md、docs/PROJECT.md、CHANGELOG.md。风险：当前尚无经过验证的数据源，不可承诺第三个平台可用。

## 官方来源

- https://open.doubao.com/apps-plugin/docs/llms.txt
- https://open.doubao.com/apps-plugin/docs/server-api/overview
- https://open.doubao.com/apps-plugin/docs/js-api/basic/getAccountInfo.md
- https://open.doubao.com/apps-plugin/docs/js-api/basic/getAccountInfoSync.md
