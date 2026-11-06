# ghost_projection：AI 可读解题说明

## 任务与证据范围

- 比赛：SCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeup/ghost_projection.md、exp/fix_outer_payload.py与recover_flag_patch_oracle.py。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

外壳修复后stage2的route projection有normally closed oracle；7字节补丁调整latch/gate参数开放隐藏字节泄漏，四epoch分别覆盖idx%4的一类。

## 按依赖顺序求解

1. 用fix_outer_payload.py修复重定位/地址关系，确认得到真实stage2。
2. 追初始化与gate字段，按recover_flag_patch_oracle.py应用7字节补丁并为logger扩RX段大小。
3. 在0x4141d8调用返回后读取尚未异或输入的AL，按0x28记录解析四epoch并按idx合并。

## 结果与验证标准

成功标准为各idx覆盖完整、重复泄漏一致及恢复输入通过原始checker。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

补丁开放oracle不是把验证强改成功；logger需保留寄存器与调用约定，单纯dump可能保留错误地址。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/exp/fix_outer_payload.py](writeups/exp/fix_outer_payload.py)
- [writeups/exp/recover_flag_patch_oracle.py](writeups/exp/recover_flag_patch_oracle.py)
- [writeups/writeup/ghost_projection.md](writeups/writeup/ghost_projection.md)
