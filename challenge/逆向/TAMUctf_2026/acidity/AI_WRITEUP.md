# acidity：AI 可读解题说明

## 任务与证据范围

- 比赛：TAMUctf 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：author_solve/brute.py、interact.py；ai_solve仅作补充。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

游戏雨点PRNG可受输入字节控制：byte复制到64位两处后混入state，经移位和乘0xf337产生bit图。目标连续14次让第17列安全，动作按四帧节奏生效。

## 按依赖顺序求解

1. 按author_solve/brute.py模拟64位xorshift，搜索使输出bit17为1的字节链。
2. 使用参考bbbcbbbccbbefb，先a移动避让，再每四帧送一个字节。
3. 等待原文39帧后d返回，观察真实Congratulations路径。

## 结果与验证标准

作者solver保存确定字节链和帧同步方法；本轮未运行游戏确认时序。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

ai_solve版本含依赖画面解析的ready策略与潜在未初始化blocks，优先作者帧同步脚本。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/ai_solve/solve.py](writeups/ai_solve/solve.py)
- [writeups/ai_solve/transcript.md](writeups/ai_solve/transcript.md)
- [writeups/author_solve/brute.py](writeups/author_solve/brute.py)
- [writeups/author_solve/interact.py](writeups/author_solve/interact.py)
