# TASK-028：未签候选采样与到账核验准备（2026-11-15）

状态：采样准备完成；**今日未签识别、新受控领取及到账实测仍未完成**。不增加GUI、不领取、不打包、不提交/推送/发布。当前未取得明确的第三方自动领取许可，不以技术可点击代替许可。

## 已实施及证据

- 复用原UIA/绑定/启动/导航和doubao_compare.capture，新增薄包装`tools/sample_doubao_day.py`。在绑定预检后正常刷新一次、滚动每日卡片但不点击，采集完整活动树；打开官方“我的奖品”供原工具保存奖励明细原始树，另存结构化明细，再关闭、复核身份并返回活动页。
- `aiclockin/doubao_session.py/.ps1`仅增加奖励弹窗保持打开/关闭选项、正常浏览器刷新。生产读取默认仍关闭弹窗；不增加领取调用。
- 独立manifest保存阶段、失败原因、身份匹配和采集日期。日期不符不读账号数据；失败、锁屏、缺字段、身份变化及页面不完整不伪造样本。不覆盖旧目录，明确unclaimed_proven=false。本地采集日期不是官方业务日期。
- 今天真实烟测：`D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/doubaowork/task028/smoke-already-signed-20261115/`，11:24:54—11:25:52；activity.json、ledger-uia.json、ledger.json、manifest.json完整，前后身份匹配、正常刷新请求已发出。官方明细仍是11-15 00:23每日签到200，正确标为已签烟测，未当作未签验证。

## 一次性采样任务

已执行并成功登记：
```powershell
D:\Python\python.exe -B tools/schedule_doubao_before.py --paired --data D:\个人开发软件\国产AI自动签到\AIClockIn\data
```
任务`AIClockIn-Doubao-Before-20261116`，下一次**2026-11-16 00:05 +08**。原Windows用户InteractiveToken、绝对路径D:\Python\pythonw.exe及源码路径；StartWhenAvailable=false、不覆盖已有任务或样本，不自动再次安排下一日。临时上限5分钟；被中断时started/incomplete不能当有效业务证据。

原生任务信息已核实Ready，NextRun UTC=2026-11-15 16:05，对应北京时间11-16 00:05，late_catchup=false。证据`task028/20261116/registration.json`和`registration-verified.json`；导出XML会省略默认false字段，故以实际任务Settings.StartWhenAvailable核实，并非只看XML字段是否存在。

输出将为`task028/20261116/before-bundle/`。电脑需原用户登录、未锁屏、未休眠且D盘可用；客户端启动/导航失败保留原因，不循环重启。任务只保存采样文件，不唤醒本聊天或执行领取。原生产任务AIClockIn-Auto不变。

## 到账核验代码的真实范围

`aiclockin/doubao_receipt.verify_delivery`为未接入提交路径的纯证据核验：要求同身份、可信完整前后奖励快照、唯一新增同日每日签到正额度行、与受控操作时段匹配。原有记录、重复行、其他任务、旧日期或无前样本都不确认。官方时间精度为分钟，提交时间单独保留；remaining保持NULL，不用额度差值补余额。

**当前UIA读取器不声称奖励列表缺项/分页已完全验证**，因此采样明确snapshot_complete=false；表头存在不等于完整前样本。核验正分支仅通过受控单元测试，不能称为真实新领取到账测试。之前真实签到及官方历史奖励记录是已有证据，不是本轮新提交的结果。

未来许可/身份/未签状态均明确后，才能把一次提交账本、官方明细回查和真实余额读取衔接；不确定只回查不重提。本轮未实施领取，也没有新的实际领取时间或领取后余额记录。

## 测试、文件及后续终止条件

新增tests/test_doubao_delivery.py、tests/test_doubao_day_sample.py；修改原receipt模块、UIA桥接模块、schedule_doubao_before.py；新增采样薄包装及本计划/结果。测试先失败再实现。

- `D:\Python\python.exe -B -m unittest discover -s tests -p 'test_*.py'`：**142通过**。
- 相关26项局部测试通过；后增错日保留失败、不打开数据目录的用例并全量验证。
- PS UTF8 Parser：0语法错误；git diff --check通过。
- 真实已签烟测通过、原生未来任务登记/下一运行时间核验通过；**未来未签采样尚未执行，受控领取及其到账没有实测**。
- providers/auth/service/store/schedule核心无修改，原账号/绑定结构及SQLite schema不变；没有新增框架依赖。

下一份样本必须有有效环境、完整活动/明细和匹配身份。若有明确当日未签/可领取标识，先核对语义与日期，不直接提交。若完整真实样本仍无明确业务状态，给出最终结论：当前纯UIA暴露信息不足以可靠识别未签，不再重复相同探针或自动续排采样。若环境失败，则说明具体原因，不把锁屏或任务未运行误判为平台状态不可读。未来样本出现前，不能预先宣称状态已解决。
