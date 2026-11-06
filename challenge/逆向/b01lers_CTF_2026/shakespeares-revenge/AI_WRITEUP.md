# shakespeares-revenge：AI 可读解题说明

## 任务与证据范围

- 比赛：b01lers CTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/solve/README.md、solve.py。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

自定义Shakespeare解释器的角色值64位、角色栈32位；截断允许构造计算器外的栈内容。revere从栈取syscall号，-1参数替换为reference指向角色栈的字符串。

## 按依赖顺序求解

1. 跟踪reference、push/pop截断和revere参数解析，确认字符串以角色栈承载。
2. 按solver输入序列利用宽度差构造/bin/sh及所需syscall参数。
3. 触发计算器退出处唯一syscall，观察是否进入预期调用路径。

## 结果与验证标准

原文报告产生shell；本地solve.py保存具体交互，未在本轮执行。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

这是解释器语义中的整数截断与系统调用接口组合，不能仅根据题目分类写成普通字符串校验。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/solve/README.md](writeups/solve/README.md)
- [writeups/solve/solve.py](writeups/solve/solve.py)
