# war-hymn：AI 可读解题说明

## 任务与证据范围

- 比赛：TAMUctf 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/solve/solve.py、decrypt_stuff.py；ai_solve.py作交叉依据。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

ELF假节名藏解密代码、密文和key。首层ks从0x67起按key[i%len]+i累加后XOR；前8字节是长度头，后续zlib得到内层，内层用RC4解四个数据块。

## 按依赖顺序求解

1. 读取.bss.secure.buffer与.init.constructors.global，去掉key尾NUL。
2. 用纯Python首层decrypt并核对zlib长度字段，解压出shared_library.so。
3. 从内层确认key=AggiesAggiesAggies及密文，分别重新初始化ARC4解每个块。

## 结果与验证标准

原solver输出三段消息和flag；内层符号DAT_00104110对应0x34字节flag密文。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

ai_solve.py会把机器码映射RWX并调用；解释算法时优先纯静态solve.py，RC4不能跨独立块复用同一流状态。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/solve/ai_solve.py](writeups/solve/ai_solve.py)
- [writeups/solve/decrypt_stuff.py](writeups/solve/decrypt_stuff.py)
- [writeups/solve/solve.py](writeups/solve/solve.py)
