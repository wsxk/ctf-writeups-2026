# Alice：AI 可读解题说明

## 任务与证据范围

- 比赛：SCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/writeup/writeup.md 的RS建模与exp.py代码块。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

macOS动态解密链最终给QR Version5/M第一RS块的24字节parity与8字节固定padding。前35字节280bit未知，可通过RS在GF(2)上的线性性建立192方程，再叠加QR模式、长度与flag格式约束。

## 按依赖顺序求解

1. 沿stage0/core.dat/alice.dat恢复RS常量和QR参数。
2. 构造固定tail基线，逐bit翻转前35字节计算parity差分，形成矩阵A及目标KNOWN_EC^base_ec。
3. 枚举payload长度加入byte-mode头、终止和格式约束，消元后重算完整RS并解析payload。

## 结果与验证标准

原文称长度29得到可打印满秩解；完整常量与exp在本题writeup内。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

欠定系统求出的一个不可打印模型不等于该长度无任何可打印解；唯一性应结合全部约束排除第二模型。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/writeup/writeup.md](writeups/writeup/writeup.md)
