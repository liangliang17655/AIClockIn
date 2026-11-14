# TASK-014 · 豆包工作最小可行性验证

日期：2026-11-14。最终目标已确认：未来支持豆包工作自动签到、额度查询及签到记录。本轮先验证真实且符合规则的数据来源；渠道通过才接入账号、GUI、SQLite；自动领取暂不实施，不开发无来源的空界面。

## 当前结论

未通过功能实施门槛，不等于断言所有方式均不可行。已查官方开发文档未提供本需求所需的个人签到/活动余额渠道；本机已登录客户端的Windows可访问性只读探测也未取得账号、今日签到或余额数据。用户已回复“找不到活动入口”，因此没有完成活动页/额度页的数据读取验证。该结果不等于账号无活动资格、登录失效、已签到或平台永远不支持。不新增豆包工作按钮、账号格式、数据库表或平台分发；原软件继续保持现有功能。

## 实际验证与证据

1. Git接入状态干净，读取AGENTS/PROJECT/TASKS/HANDOFF。未运行任何真实签到。
2. 发现客户端安装元数据，但默认LOCALAPPDATA/Application未找到启动程序；通过已有开始菜单链接定位到D盘自定义安装目录。启动器ProductVersion=2.30.1、实际进程二进制版本=147.0.7727.149（Chromium内核口径），签名Valid；卸载注册表DisplayVersion=2.25.18，与二进制口径不同，不能据此断言客户端过旧或活动不可用。没有安装、升级或重启客户端。
3. 最初未运行；用户回复“已登录，我会保持窗口打开”后检测到真实客户端进程。Windows UIAutomation库可用，主窗口可见。初次主窗口只有4个后代控件（3 Pane、1 Button），未暴露业务文本。再按所有目标进程查询顶层窗口，发现2个可见窗口，分别4/14个后代（Pane/Button），没有Text/Document业务控件或严格匹配的签到/额度标签。未读取或记录会话内容、昵称、手机号、Cookie。
4. MSAA标准可访问性入口调用HRESULT=0，客户端根对象仅有1个直接子节点；这不证明深层MSAA永远不可读，未将其当作全面否定。一次额外UIA属性探针使用了本机.NET不存在的Legacy属性，返回参数错误；后改用GetSupportedPatterns确认可用模式。该探针错误没有作为客户端不支持的证据。
5. 只读查看本机9342监听未发现现成通道；未设置CDP参数、未导出Cookie、未读取Cookie数据库、未复刻签名或设备信息、未调用私有活动POST。端口缺失不代表官方客户端损坏。
6. 用户最终回复“找不到活动入口”。本轮无法取得活动页真实数据样本，页面级验证未执行；不能将其报告为活动页接口失败或账号活动不可用。

外部本机证据位于D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/：environment-probe.json（登录前）、uia-probe.json、readonly-feasibility.json。不含凭据，未上传GitHub。临时可访问性辅助编译文件仅位于D工作区temp。

## 官方渠道核查

- [服务端API总览](https://open.doubao.com/apps-plugin/docs/server-api/overview.md)：已查列表为应用级身份、订单支付、进行中任务、通知等，没有看到个人每日签到/个人活动额度查询。需要开发者应用及后端保管AppSecret，不可把密钥放EXE或Git。这不是“所有内部接口不存在”的结论。
- [登录接入](https://open.doubao.com/apps-plugin/docs/backend-development/login)：OAuth用于豆包调用第三方MCP/业务账号，以及应用内OpenID识别；不等于授权AIClockIn获得官方客户端Cookie或个人活动额度。
- [SAEP官方接入指南](https://o.doubao.com/SAEP_Protocol/saep-access-documentation)：属于Android/ObricUI平台屏幕自动化策略，不是Windows豆包工作只读接口，不能挪作本项目授权依据。
- [活动规则](https://lf3-cdn-tos.draftstatic.com/obj/ies-hotsoon-draft/incentive-campaign-rules/f7f2c423-c770-44e7-9be4-bd67a28f074e.html)：要求官方认可方式，列明非官方客户端/插件/群控/多账号等违规情形；双PC端共享进度奖励不重复。本轮继续不实施领取。官方条款以客户端实际适用规则为准。

前轮已审查agent-checkin的CDP活动页方案和Agent2API/Agent2Providers的Cookie/私有请求方案；它们不能替代官方授权，亦未作为已验证数据源接入。AGPL实现不复制/翻译进当前MIT应用。

## 准入标准与后续扩展契约

只有以下全部成立才实施：确认允许的读取方式；可验证账号身份；取得真实今日状态和额度样本；字段语义/新鲜度清楚；无须改设备身份、复制受保护会话或私有签名；可在客户端不可用时准确返回未知。状态、奖励金额、剩余额度不能相互推算。

后续适配边界（仅文档契约，无空实现）：

- initialize_official_login：官方流程，绑定可验证身份。
- query_status：返回identity/login_state/day/checkin_state/earned/remaining/evidence_source/observed_at/partial_errors；未知为None，不当0。
- capabilities：查询/领取独立声明。未确认渠道时query=False；claim=False。只读成功绝不自动放开领取。
- claim_daily：仅在找到平台允许方式并再次确认后实现，含提交前持久化、同账号同日同活动去重、结果待确认只回查不重复提交。

这些是接入边界，不新增插件框架或通用平台重构。现有WorkBuddy/Trae分发和签到核心保持不动。

## 当前替代路径与下一步

A. 如果以后能通过官方帮助定位到活动/额度入口，可再次进行页面级只读验证。当前不要求用户反复尝试，也不以调试参数或Cookie解密作为自动回退。
B. 请求官方提供个人只读查询文档/授权或客户端可访问性支持。能访问页面或调试接口不等于获得平台许可。
C. 如果本人选择官方升级后复测，可再验证UI数据是否暴露；不擅自升级客户端，也不承诺升级一定解决。
D. 人工在官方客户端查询/领取仍可用；人工整理记录只能标记“人工记录”，不包装成自动功能，本轮未实现。

本轮没有真实状态/余额样本，未进行SQL入库验收或平台集成测试；没有业务代码变化，不重复运行全量回归或打包。验证不通过就不加入空界面、不发布新版本。未来自动签到目标保留，不把当前阶段永久缩减为网页入口。


## 本轮收尾

用户确认找不到活动入口，本轮最小验证以“未通过接入门槛”收尾，而非继续等待页面打开。替代路径为取得官方只读接口/授权、官方帮助确认入口适用范围，或客户端可访问性支持后重新验证；均未作为已存在能力承诺。自动签到/额度/记录的最终目标保留，但无真实数据来源时不开发空界面。本轮仅维护研究和交接文档，未修改业务代码/账号/库/任务/安装包，未提交推送；文档git diff --check通过，不重复跑业务测试。


TASK-014 current recheck (2026-11-14): entry found and manual claim confirmed by user; actual app 2.36.15 and running process verified. Business read source remains unverified; UI connection unavailable. No implementation or package changes. Current evidence, changed files, validation limits and next steps: docs/DOUBAOWORK-RECHECK.md (DOUBAOWORK-RECHECK.md from docs/).
