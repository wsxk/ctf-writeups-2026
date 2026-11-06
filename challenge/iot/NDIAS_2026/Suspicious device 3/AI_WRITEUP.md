# Suspicious device 3 — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：iot｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是在内部DB主机读取受flagreader组保护的stage3文件。链路为数据库泄露维护账户→内部SSH→SGID工具的TOCTOU，权限提升目标是组读取能力。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第97—101页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 从maintenance_users找到dbmaint账户，借stage1云端命令通道连接iot-db SSH；官方示例密码Maint@2026!属于赛事环境。

2. 检查/home/flagreader/flag_stage3.txt权限及/usr/local/bin/db_diag_report，后者带flagreader SGID。

3. 逆向工具：路径必须位于/tmp/dbdiag/；lstat拒绝符号链接并要求文件owner等于真实UID；之后usleep(200000)，再按原路径open读取。

4. 在受控复现里先提供自己拥有的普通文件通过检查，在200ms窗口将同一路径替换为指向flag的符号链接。open跟随新目标，程序仍具有flagreader有效组。

5. 读取stdout并保留成功证据；失败时区分路径前缀、owner和竞争时序，不能把普通dbmaint权限说成root。

## 结果与验证

验证需看到stage3文件内容，而不是仅看到SSH登录或SGID位。漏洞根因是检查的文件与使用的文件未绑定到同一个已打开描述符。

## 复现边界与易错点

官方第101页提供反编译逻辑，本地不含独立完整竞争脚本；本文仅静态整理，没有进行跨主机连接。

附件登记状态：部分。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
