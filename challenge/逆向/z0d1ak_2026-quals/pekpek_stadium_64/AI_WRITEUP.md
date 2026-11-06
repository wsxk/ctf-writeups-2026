# pekpek_stadium_64：AI 可读解题说明

## 任务与证据范围

- 比赛：z0d1ak CTF Qualifiers；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：1_README.md 的byte order与CRC-state recovery。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

v64相邻字节交换后露出N64 ELF和SYMT。真实locker只依赖16字节key的32位CRC状态，因此可用已知zdk{前缀与尾部CRC求有效状态，不必恢复原key。

## 按依赖顺序求解

1. 规范化v64→z64，解析符号并定位unlock_cart_memory和0x3460c的96字节locker。
2. 枚举合法长度1..90，对CRC递推建32位约束并利用已知明文过滤状态。
3. 由候选状态生成流解密，解析大端长度及尾CRC验证完整payload。

## 结果与验证标准

原文结果 zdk{httPS://YOuTu.8E/tS2HZ5jwSJw?si=nnTOse6QlJEcB0u_}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

嵌入MIO0/GBA程序的明文flag是诱饵；结果URL是字面答案无需访问。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/1_README.md](writeups/1_README.md)
