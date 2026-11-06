# starless-c：AI 可读解题说明

## 任务与证据范围

- 比赛：LA CTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：community/README.md、solve.py与official/solve.txt。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

自修改迷宫状态包含当前位置和5个active token。移动到active格会消耗它并激活特定save target，f路径要求指定五格同时active。

## 按依赖顺序求解

1. 提取23个映射单元的方向与save映射，记录真实内存布局。
2. 将状态建成(position,active_set)，搜索达到目标active集合的路线。
3. 过滤未映射67693相关路径，重放后再按f进入完整flag链。

## 结果与验证标准

原文结果 lactf{starless_c_more_like_starless_0xcc}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

静态存在跳转不等于目标页已映射；忽略缺页会产生不可执行解。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/community/README.md](writeups/community/README.md)
- [writeups/community/solve.py](writeups/community/solve.py)
- [writeups/official/solve.txt](writeups/official/solve.txt)
