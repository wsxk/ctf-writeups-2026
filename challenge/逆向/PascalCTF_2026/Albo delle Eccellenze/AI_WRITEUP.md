# Albo delle Eccellenze：AI 可读解题说明

## 任务与证据范围

- 比赛：PascalCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：maksimhayder.html 中 [Reverse] Albo delle Eccellenze 章节。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

代码生成器的strcmp相等返回1，但main又xor eax,1导致分支反转：不匹配硬编码A11D612LPSCBLS37反而进入读flag路径。

## 按依赖顺序求解

1. 分别跟踪检查函数返回值与main分支，确认最终条件反转。
2. 提供合法格式而不匹配常量的姓名、生日、性别、出生地输入。
3. 检查是否到达fopen("flag")；本地需测试flag文件，远程才有真实结果。

## 结果与验证标准

原文结果 pascalCTF{g00d_luck_g3tt1ng_your_pr1zes_n0w}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

不能笼统称所有输入都接受，仍需通过字段解析；本地Could not open flag已说明到达读文件路径。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/maksimhayder.html](writeups/maksimhayder.html)
