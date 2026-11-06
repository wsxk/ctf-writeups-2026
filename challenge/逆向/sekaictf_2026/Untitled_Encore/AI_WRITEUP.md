# Untitled_Encore：AI 可读解题说明

## 任务与证据范围

- 比赛：SekaiCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：1_writeup.txt 的Untitled Encore章节。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

Windows PE内嵌0xbb8字节eBPF ELF，rodata又藏388字节按PC异或编码的验证器。32个chart字节直接校验后，VM输出和parser聚合状态参与最终32字节自定义hash。

## 按依赖顺序求解

1. 定位内嵌ELF和嵌套验证器，按PC keystream解码。
2. 恢复32个chart约束并仿真eBPF的32字节比较，保持parser状态。
3. 模拟原始byte-mixing hash，以chart、VM输出和聚合状态派生flag key并解密。

## 结果与验证标准

原文结果 SEKAI{eBPF_my_B3l0v3d}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

同博客含11题，勿把其他题flag或区块链利用混入；hash为自定义，不能换成标准SHA。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/1_writeup.txt](writeups/1_writeup.txt)
