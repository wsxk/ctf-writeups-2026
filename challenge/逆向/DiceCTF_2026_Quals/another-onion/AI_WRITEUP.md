# another-onion：AI 可读解题说明

## 任务与证据范围

- 比赛：DiceCTF 2026 Quals；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：community/README.md及official解法代码。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

多层自解密代码每层消耗2字节key，SHA-NI产生密钥流；正确key解出符合下一层模板的代码，因此每层只需搜索65536候选。

## 按依赖顺序求解

1. 定位层边界和read调用，建立下一层含两次read@plt的结构判据。
2. 在隔离副本中模拟单层，替换输入并阻止继续跳转，枚举2字节候选。
3. 保留正确解密状态逐层推进；实际实例256层，需共享只读BSS和并行实现满足时限。

## 结果与验证标准

原文报告取得提交token及dice{5p33d_1s_a1s0_imp0rtant_1n_r3ver5e_3ngineer1ng}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

示例8层与正式256层的转移指令和BSS范围不同；模板匹配后还需执行最终验证。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/community/README.md](writeups/community/README.md)
- [writeups/official/README.md](writeups/official/README.md)
- [writeups/official/solution/asmhelp.py](writeups/official/solution/asmhelp.py)
- [writeups/official/solution/compile-solve.sh](writeups/official/solution/compile-solve.sh)
- [writeups/official/solution/e2e_solver_submit.py](writeups/official/solution/e2e_solver_submit.py)
- [writeups/official/solution/solve.c](writeups/official/solution/solve.c)
- [writeups/official/solution/solve.py](writeups/official/solution/solve.py)
- [writeups/official/solution2/solve_onion.py](writeups/official/solution2/solve_onion.py)
