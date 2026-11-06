# the-fish：AI 可读解题说明

## 任务与证据范围

- 比赛：LA CTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：official/solve.py 的solve与gen互逆流程。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

Fish程序先将UTF-8输入大端拼整数，再用变体Collatz把奇偶路径编码进大整数。官方逆算法从acc=1遍历target低位：先倍增，若位为1则减1再除3。

## 按依赖顺序求解

1. 从Fish解释器还原数值变换并提取完整target，避免抄错903位整数。
2. 按official/solve.py逆遍历，直到curr=1，恢复原大整数。
3. 按最小长度大端转字节，再用官方gen重编码与原target比较。

## 结果与验证标准

原文结果 lactf{7h3r3_m4y_83_50m3_155u35_w17h_7h15_1f_7h3_c011472_c0nj3c7ur3_15_d15pr0v3n}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

对这个有限输入验证不需要证明Collatz猜想；不能把社区泛化描述当数学定理。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/community/README.md](writeups/community/README.md)
- [writeups/official/solve.py](writeups/official/solve.py)
