# SU_Protocol：AI 可读解题说明

## 任务与证据范围

- 比赛：SUCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeup/SU_Protocol…md 的结构体/封包代码及反调试说明。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

Themida保护的协议检查器在运行时修改TEA key/delta。payload嵌于121字节结构，要求反序列化首字节0x60与opcode0x55；最终flag是完整封包hex字符串的MD5。

## 按依赖顺序求解

1. 从运行时段名取得key，核对父进程触发的修补路径及实际delta。
2. 按原文字段表填结构并以正确key/delta执行TEA，验证重叠字段和补码约束。
3. 外包#与换行后再hex编码，对最终字符串按原文方法MD5。

## 结果与验证标准

原文结果 SUCTF{ad1b51464c1b679fe731c7d718af241f}；设计允许多解。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

父进程explorer.exe/cmd.exe可将delta改为0x9E3779B0；静态值未必是运行值，hash对象层级不能错。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/writeup/SU_Protocol 31bef3f8bbc880d98410dd9efed3e0d2.md](writeups/writeup/SU_Protocol%2031bef3f8bbc880d98410dd9efed3e0d2.md)
