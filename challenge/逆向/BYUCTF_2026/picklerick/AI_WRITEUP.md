# picklerick：AI 可读解题说明

## 任务与证据范围

- 比赛：BYUCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/readme.md 与solve.py。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

pickled.txt用单词承载二进制：pickle映射1，其他token映射0；每8bit转字节后再XOR 0x67，恢复ELF。

## 按依赖顺序求解

1. 按空白分词并保留顺序，形成位串。
2. 每8bit按高位在前解析，逐字节XOR 0x67并写为unpickled_elf。
3. 检查ELF魔数和结构，再定位其中真正的flag检查或输出。

## 结果与验证标准

原文给出 byuctf{1m_p1ckl3_r1111ck!}；solve.py本身只恢复文件，不证明该flag已通过执行验证。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

本题与Python pickle反序列化无关；未知token一律0是原solver假设，应核对题目字典。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/readme.md](writeups/readme.md)
- [writeups/solve.py](writeups/solve.py)
