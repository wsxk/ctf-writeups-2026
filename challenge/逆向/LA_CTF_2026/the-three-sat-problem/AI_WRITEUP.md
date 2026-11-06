# the-three-sat-problem：AI 可读解题说明

## 任务与证据范围

- 比赛：LA CTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：community/README.md、solve_sat.py；official/solve.txt。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

1279个0/1字符承载SAT赋值，main额外要求bit754=1；大验证函数组合OR子句及AND。关键工作是忠实抽取SSA依赖而非盲删矛盾条件。

## 按依赖顺序求解

1. 恢复每个内存bit及取反临时值，建立子句和bit754约束。
2. 若UNSAT，回查SSA数据流；社区删除一子句只是怀疑提取错误，不能因此修改真实题意。
3. 使用官方solve.txt作为参考赋值，逐条核验原二进制判定及flag生成。

## 结果与验证标准

社区给lactf{is_the_three_body_problem_np_hard}，官方另保存完整1279位输入。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

社区称2848子句并删除其中一条的做法未构成正确性证明，应以原检查器或修正提取器验证。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/community/README.md](writeups/community/README.md)
- [writeups/community/solve.py](writeups/community/solve.py)
- [writeups/community/solve_sat.py](writeups/community/solve_sat.py)
- [writeups/official/solve.txt](writeups/official/solve.txt)
