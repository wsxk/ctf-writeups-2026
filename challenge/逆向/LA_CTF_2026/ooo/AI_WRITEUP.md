# ooo：AI 可读解题说明

## 任务与证据范围

- 比赛：LA CTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：official/solve.py优先，community/README.md用于语义说明。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

同形Unicode函数名遮蔽简单算术，实际相邻码点满足x[i]+x[i+1]=arr[i]。官方solver从'l'开始递推x[i+1]=arr[i]-x[i]。

## 按依赖顺序求解

1. 用Unicode码点重命名每个函数，按运算语义化简嵌套表达式。
2. 采用official/solve.py的27个整数，以ord('l')顺序相减生成28字符。
3. 输出各字符码点并原样UTF-8提交，核对原程序实际循环范围。

## 结果与验证标准

官方solver提供确定恢复法；社区文档标为Verification Issue Pending，因此这里不声称已运行通过。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

社区文档比赛年份与目录不同，且对最后一对约束存在讨论；不要手工替换看似相同的o字符。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/community/README.md](writeups/community/README.md)
- [writeups/official/solve.py](writeups/official/solve.py)
