# ML Connoisseur：AI 可读解题说明

## 任务与证据范围

- 比赛：UofTCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/solve/solve.py、deobfuscate.py、deobbed_model.py。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

混淆神经网络实为可逆加性coupling串。每块先逆通道线性mix，再用x2=y2-G(y1)、x1=y1-F(x2)恢复；无需逆ReLU或训练模型。

## 按依赖顺序求解

1. 由obf_map解析packed卷积权重和opcode，识别SPLIT/F/G/CONCAT/MIX块边界。
2. 从get_ref的z_ref逆序各块，保留寄存器SWAP/SHUF以正确执行F/G子程序。
3. depth_to_space后逆像素排列，再撤销mu/sigma归一化，输出PNG并正向模型比较参考张量。

## 结果与验证标准

solve.py输出flag.png；完整重构依赖weights.pt、dist.model及obf_map.json。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

通道mix须可逆；浮点与uint8取整会引入误差，应在保存前后分别报告forward误差，不能仅看图形似flag。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/solve/deobbed_model.py](writeups/solve/deobbed_model.py)
- [writeups/solve/deobfuscate.py](writeups/solve/deobfuscate.py)
- [writeups/solve/original.py](writeups/solve/original.py)
- [writeups/solve/solve.py](writeups/solve/solve.py)
