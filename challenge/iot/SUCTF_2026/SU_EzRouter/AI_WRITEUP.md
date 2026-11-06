# SU_EzRouter — AI 易理解版 Writeup

> 比赛：SUCTF 2026｜目录分类：iot｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

现有材料只有exp.py。它的静态行为是先借auth参数取得session，再安排WiFi/黑名单状态，最后提交含amd64 shellcode的VPN配置；漏洞根因需要结合CGI二进制进一步确认。

## 材料与证据

- [writeups/exp/exp.py](<writeups/exp/exp.py>)

## 推导与解题步骤

1. 阅读login_bypass：请求`/www/http?action=login&auth=1`，代码把cookie中存在session_id当登录成功条件，后续复现还应验证实际权限。

2. 调用wifi.cgi保存短ssid/password，再通过list.cgi添加7条black条目；这说明利用对状态/内存布局有前置依赖，不能删掉。

3. set_vpn向vpn.cgi提交JSON，pass为0x19个字符，cert字节为00 e9 f2 00 00 00，custom为shellcode填充到0x7eb后补NUL。custom字节被B64:前缀编码，其他bytes转\xNN文本。

4. shellcode旨在把题目flag写入./www/flag.html。检查服务端对字段的解码、内存拷贝和控制流后，才能判断跳转字节与落点。

## 结果与验证

脚本没有flag输出或成功日志，edit_vpn和apply_vpn整个触发段被三引号注释。只能确认“作者构造的利用输入”，不能宣布完整利用链已运行成功。

## 复现边界与易错点

不应臆造具体堆漏洞名、覆盖偏移或已取得shell。当前缺口：CGI根因、最终触发条件、输出读取与成功验证。依赖requests和pwntools，且context.arch=amd64。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
