# challenge7：AI 可读解题说明

## 任务与证据范围

- 比赛：TAMUctf 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/solve/recover_inner_payload.py和solve_inner.py。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

外层ELF用.text SHA与候选32字节常量形成bind，bind同时解碎片并参与SHA规则选择。恢复动作链得到内层，再逆37字节目标的逐字节add/XOR流。

## 按依赖顺序求解

1. 从.rela.dyn和.data.rel.ro恢复chunk表，.rodata扫描52字节规则记录。
2. 枚举bind候选并匹配stage0哈希，按prepend/append/replace/delete/execute规则模拟至结束，输出内层。
3. 按solve_inner.py从state=0x1337C0DE^0xC0DEF00D推key/add并恢复body，同时核对acc、score、digest和next_token。

## 结果与验证标准

脚本输出gigem{37字节body}及多项中间摘要，可作为独立检查点。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

外层扫描采用结构启发式，换构建需核对表边界；仅得到某个可运行payload不证明所有规则推导正确。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/solve/recover_inner_payload.py](writeups/solve/recover_inner_payload.py)
- [writeups/solve/solve_inner.py](writeups/solve/solve_inner.py)
