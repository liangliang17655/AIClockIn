# 来源与许可

AIClockIn 为独立应用仓库；应用结构、结构化结果、HTTP、平台执行流程、存储、界面与自动任务在本项目重新编写，不在运行时依赖旧项目。

## 有限复用

`aiclockin/workbuddy_auth.py` 仅复用/适配 `huxc573/AICreditPunch` 的 MIT 本机 WorkBuddy 登录发现与解密适配（v1.9.2 相关部分），保留必要的解析和 WorkBuddy Electron 本机绑定协议。没有整体复制旧签到脚本。对应版权许可全文如下：

MIT License

Copyright (c) 2026 huxc573

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 接口行为参考

Trae CN 登录、刷新和签到接口行为参考 AICreditPunch 的验证流程；该来源注明 Trae 链路源自 MIT 项目 xz0609/trae-work-checkin-ql（Copyright (c) 2026 Yiran），OAuth 参考 Maquer/trae-signin（Copyright (c) 2026）。新执行流程没有导入其源模块；为清楚保留溯源及可能的衍生关系，随附相应 MIT 声明，不声称严格 clean-room。

MIT License

Copyright (c) 2026 Yiran
Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
