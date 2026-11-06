# Gateway Gremlins — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是串联遗留Web漏洞和CAN鉴权。Web链泄露算法，CAN nonce使密钥具有时效；仅拿到配置不等于完成解锁。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第11—18页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 从robots.txt发现`/legacy/`。旧登录使用XML/XPath鉴权，经XPath注入进入diagnostic upload；此处不是SQL数据库注入。

2. 上传含外部实体的XML读取`/app/config.json`，再按.bak提示读取`/app/config.json.bak`，备份里才包含完整密钥逻辑。

3. 监听CAN ID0x555，将前4字节按大端解析为nonce。进入`10 03`会话，发送`27 05`取得seed。

4. 计算`key=(rol32(seed ^ 0x5A17C0DE ^ nonce,7)+0x27110027)&0xffffffff`；以4字节大端发送`27 06`。nonce滚动时重新获取并重试，必要时重取当前seed。

5. 解锁成功后读取`22 F1 A0`，剥离`62 F1 A0`响应头再解码。

## 结果与验证

每个阶段的证据依次是登录会话、配置备份中的算法、当前nonce、67 06正响应以及F1A0数据；PDF未在本题代码中列最终flag。

## 复现边界与易错点

端点及常量仅适用于比赛环境。必须保持nonce与提交时刻一致；原文省略了通用UDS收发函数，可参考相邻Seed-Key Leak的结构。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
