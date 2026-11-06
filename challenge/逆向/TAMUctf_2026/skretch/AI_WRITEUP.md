# skretch：AI 可读解题说明

## 任务与证据范围

- 比赛：TAMUctf 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/poc/fast.py、make_eqs.py，对照slow.py。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

图像字节先加i+1模256，再以循环三对角方程A[i]x[i-1]+B[i]x[i]+C[i]x[i+1]=R[i]编码。稀疏矩阵使大PNG系统可解。

## 按依赖顺序求解

1. 按eqs.txt构建含首尾环绕的CSR三对角矩阵。
2. 用spsolve解并舍入，必须以整数重新计算每条方程验证残差为0。
3. 对解字节减i+1模256，写PNG并核对PNG结构及图像内容。

## 结果与验证标准

fast.py输出solve.png；make_eqs.py提供前向生成规则，可独立验证。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

slow.py不仅稠密矩阵耗内存，还漏首尾环绕项，不应作为正确替代；浮点舍入需要整数校验。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/poc/fast.py](writeups/poc/fast.py)
- [writeups/poc/make_eqs.py](writeups/poc/make_eqs.py)
- [writeups/poc/slow.py](writeups/poc/slow.py)
