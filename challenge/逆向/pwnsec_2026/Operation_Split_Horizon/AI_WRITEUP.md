# Operation_Split_Horizon：AI 可读解题说明

## 任务与证据范围

- 比赛：PwnSec CTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：1_README.md 的分层协议及fragment routing。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

PCAP含多阶段投递和分流外传。先AES-CBC/HMAC解dropper，再过XTEA类loader和SBVM4；C2用逐消息更新key的ChaCha20，最后数据拆在HTTP cookie与DNS并以截断HMAC标记。

## 按依赖顺序求解

1. 按TCP流导出HTTP对象，UTF-16LE解PowerShell，恢复异或拆分AES key并验证HMAC。
2. 解loader到stage3，按捕获顺序重算C2 ratchet和SBVM4输出。
3. 同时收集cookie和DNS碎片，以HMAC匹配排序并重组解密外传内容。

## 结果与验证标准

原文结果 pwnsec{a41f2691c3f1bcf72d0ec060c70d6ce7}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

不得只读一个通道或乱序解C2；缺PCAP/中间数据时无法复算。本文仅离线分析捕获材料。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/1_README.md](writeups/1_README.md)
