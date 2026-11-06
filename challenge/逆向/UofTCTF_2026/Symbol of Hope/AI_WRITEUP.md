# Symbol of Hope：AI 可读解题说明

## 任务与证据范围

- 比赛：UofTCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/solve/solve.py。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

UPX解包后的checker可用angr符号执行，以stdout包含Yes作为成功状态。solver建44个8位符号输入并加uoftctf前缀与位置41的右花括号。

## 按依赖顺序求解

1. 先解UPX并核对产物路径checker，建立含换行的SimFileStream。
2. 使用full_init_state，添加前缀及原脚本位置约束，探索成功输出路径。
3. 将找到的完整字节模型送回原checker并记录实际读取长度/终止处理。

## 结果与验证标准

现有资料为angr solver，未附本轮求得模型；成功应以原checker为准。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

flag_len=44但右花括号在flag_len-3，需要核对后两字节用途；has_end=False可能允许额外符号输入，不能忽略实际消费字节。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/solve/solve.py](writeups/solve/solve.py)
