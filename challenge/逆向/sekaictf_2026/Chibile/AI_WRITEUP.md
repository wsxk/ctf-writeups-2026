# Chibile：AI 可读解题说明

## 任务与证据范围

- 比赛：SekaiCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：1_README.md 的三项逆向任务和Phase1/2。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

游戏秘密门、UM和KM attestations、两阶段加密协议构成依赖链。KM可函数模拟，最终两个12字符秘密由BK及服务lh/c值经HMAC/rotate派生。

## 按依赖顺序求解

1. 解exe秘密门phrase与host，解UM DLL的XOR/ARX壳并定位ordinal1。
2. 针对同nonce计算UM与KM，构造CBL2的RSA-OAEP/AES-CBC/HMAC封包完成Phase1。
3. 按PROTOCOL扫描32字节BK窗口，筛出指定字母表的两个12字符码，复用sid提交Phase2取CBF2 PNG。

## 结果与验证标准

原文结果 SEKAI{Th4nk5_F0R_Pl4y1ng_My_Chibi_G4m3__5t4y_tun3d_f0r_my_n3xt_0n3}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

阶段nonce、sid和attestation必须对应同连接；本轮未加载驱动或连接历史服务。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/1_README.md](writeups/1_README.md)
