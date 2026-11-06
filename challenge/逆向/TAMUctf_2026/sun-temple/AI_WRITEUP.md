# sun-temple：AI 可读解题说明

## 任务与证据范围

- 比赛：TAMUctf 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/scripts/find_solution.py与find_solution_fast.py。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

2736字节blob按三字节指令解析，type/variant/operand决定成本，最多12个rite及其顺序提供折减和交互。目标分数<=3415150，是序列优化而非直接解密。

## 按依赖顺序求解

1. 解析generated_chamber.h并确认长度，预聚合相同type/variant的权重。
2. 按整数除法、MIN_FACTOR180和顺序交互实现score，以greedy初始再做交换/插入/替换退火。
3. 找到达标序列后逐项重算成本，按每项rite十六进制+位置十六进制编码提交。

## 结果与验证标准

脚本输出order、hex、score与pass；没有静态证明其一定找到全局最优，也无需全局最优只需达标。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

随机重启没有固定时限或成功保证；任何浮点化简可能改变整数截断后的分数。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/scripts/find_solution.py](writeups/scripts/find_solution.py)
- [writeups/scripts/find_solution_fast.py](writeups/scripts/find_solution_fast.py)
