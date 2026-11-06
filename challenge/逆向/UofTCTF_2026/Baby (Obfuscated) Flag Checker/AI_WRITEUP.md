# Baby (Obfuscated) Flag Checker：AI 可读解题说明

## 任务与证据范围

- 比赛：UofTCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/solve/solve.py、baby.py与flag.txt。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

solver用自定义输入对象替代字符串，__getitem__记录切片索引，__eq__记录比较常量并返回True，从而让混淆检查器继续暴露后续约束。

## 按依赖顺序求解

1. 阅读baby.py定义gog0sQu1D后的检查流程，确认可由Python对象代理承载。
2. 设置hook_s(74)，对切片组合保持索引映射，捕获每个(idxs,expected)。
3. 将常量按索引填回74字符数组，检查重叠一致并以真实字符串跑原函数。

## 结果与验证标准

writeups/solve/flag.txt保存参考74字符结果；代理一路返回True只是采集，不能证明填回字符串通过。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

原solver exec加载未知Python，未在本轮运行；若其他字符串方法或隐式转换存在，代理语义需补全。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/solve/baby.py](writeups/solve/baby.py)
- [writeups/solve/flag.txt](writeups/solve/flag.txt)
- [writeups/solve/solve.py](writeups/solve/solve.py)
