# Mystery：AI 可读解题说明

## 任务与证据范围

- 比赛：bhackari CTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：1_writeup.txt 的 Reverse — Mystery 节。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

mystery.so在初始化时哈希自身：SHA-256与CRC32生成64字节表和四个stage值，再混合成AES-256-CTR key。所有关键材料均来自给定文件，可离线重算。

## 按依赖顺序求解

1. 对未修改so计算sha和noise，按原文64位截断规则生成table0。
2. 计算四个stage公式，再模拟(value^0xcafebabe)-index*0x1234的存储变换。
3. 重现reveal密钥链，用全零16字节IV解密flag.enc。

## 结果与验证标准

原文结果 bhackariCTF{F1n4lly_th4_My$t3rY_!S_$OlvEd!!!}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

修改so会改变自身哈希；easy_access的BhackariCTF是诱饵，不能当作结果。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/1_writeup.txt](writeups/1_writeup.txt)
