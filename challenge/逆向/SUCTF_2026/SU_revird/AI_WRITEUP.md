# SU_revird：AI 可读解题说明

## 任务与证据范围

- 比赛：SUCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeup/writeup.md 的worker/driver分析及exp/exp.py。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

表面main的XOR检查为假flag，真实入口解PE并进程镂空启动worker，再通过Revird驱动组合R3/R0两份AES轮密钥。实际密码还改了S盒、opcode组合并多一层ShiftRows。

## 按依赖顺序求解

1. 追实际入口sub_140002FC0→2F00，提取解密后的0x440f PE与设备IOCTL数据流。
2. 从用户层与驱动分别恢复key扩展，轮密钥按位XOR，建立真实S盒与轮操作顺序。
3. 按CBC逆块并异或前块/IV，校验padding后恢复48字节flag。

## 结果与验证标准

原文结果 SUCTF{D0_y0U_unD3r5t4nd_Th15_m491c4l_435?_41218}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

标准AES库不能直接替代魔改轮函数；CheckRemoteDebuggerPresent会污染后续API hash。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/exp/exp.py](writeups/exp/exp.py)
- [writeups/writeup/writeup.md](writeups/writeup/writeup.md)
