# squ1rrel_o_tron：AI 可读解题说明

## 任务与证据范围

- 比赛：squ1rrel CTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：1_README.md 的custom insn、SBOX与4096轮说明。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

PDF内嵌TinyEMU asm.js和RISC-V Linux，chall使用只在修改模拟器中实现的两条自定义指令。funct7=0x7e设置状态，0x7f用S盒和状态执行混合。

## 按依赖顺序求解

1. 从PDF JS的embedded_files做base64/zlib提取，取得chall和模拟器数据。
2. 解析opcode0x33下两个额外分支及heap SBOX，保持32位语义实现F。
3. 执行4096轮变换把32字节nonce映为16字节响应，依次回答5轮。

## 结果与验证标准

原文结果 squ1rrel{why_run_l1nux_0n_4_pr1nt3r_wh3n_y0u_c4n_run_l1nux_0n_4_pdf}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

标准QEMU不支持这两条指令；不可将SIGILL归因于普通加载错误。远程每轮时限5秒。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/1_README.md](writeups/1_README.md)
