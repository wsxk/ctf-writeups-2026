# PwnSec_Support — AI 可读解题说明

- 比赛：PwnSec CTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

从工单站的guest权限链读出L3afVM数据区flag。

工单ID拼接SQL允许堆叠语句创建管理员session，admin Lua的note_save提供guest任意32位写；修补ticks返回类型将写原语转为字符串读。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 解析ctf_sql.l3af的十六进制DATA模块，恢复/ticket与/admin源码，确认session表及root user_id=1；先明确注入和验证token的字段。
2. 在/ticket?id中结束查询并INSERT自选session，再带token进入admin Lua；这一步仅获得guest Lua执行。
3. 按加载器从0x10000开始、DATA四字节对齐、代码16字节对齐且前置两条指令的规则计算符号地址。
4. 用tostring(ticks)泄露remote embedded_ticks地址，减本地符号得到code slide；FLAGPAD大小变化会平移代码，不能硬编码本地地址。
5. 以note_save把ticks中的CALL改为LC R0,address，并把lua_pushinteger目标改为lua_pushstring；在remote代码段前512字节内读NUL结尾字符串，定位pwnsec格式flag。

## 验证标准与结果

原文报告 pwnsec{fa6fa484ff74c09a}。验证链应留存session认证、函数地址差、补丁前后指令和最终返回字符串；guest内存读不等于宿主逃逸。

## 限制与易错点

本地只有README，独立solve.py未收录；完整SQL语法与指令布局以原文代码块和附件为准。改变本地监听8081是作者环境调整，不是利用必需条件。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
