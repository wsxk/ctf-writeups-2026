# angr_management：AI 可读解题说明

## 任务与证据范围

- 比赛：BYUCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/writeup.md、solve.py。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

GOTO迷宫可以转为main内部控制流图上的路径问题。若保留printf/puts/get_input节点，调用与返回边会造出虚假捷径；需先删去这些非迷宫节点。

## 按依赖顺序求解

1. 用angr取main入口与出口对应CFGNode，过滤库函数/输入辅助函数节点。
2. 用networkx.shortest_path找有效基本块路径。
3. 对路径边仅提取Ijk_Boring且stmt_idx!=-2的目标编号，依次输入。

## 结果与验证标准

原文结果 byuctf{g3t_w1th_th3_c0ntr01_fl0w}；验证完整跳转序列实际到达终点。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

最短CFG路径不自动等于可行输入，必须使用原文的边筛选规则。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/solve.py](writeups/solve.py)
- [writeups/writeup.md](writeups/writeup.md)
