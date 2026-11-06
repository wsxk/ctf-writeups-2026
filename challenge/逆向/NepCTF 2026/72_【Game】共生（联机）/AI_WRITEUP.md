# 【Game】共生（联机）：AI 可读解题说明

## 任务与证据范围

- 比赛：NepCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/writeup.md 的#72与proven_run.py。
- 附件登记状态：缺失。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

联机完成流程同时依赖HTTP注册及UDP双端状态机。host/guest必须不同team_token，否则DupTeam使后续NotInGame；RunComplete还检查进度时机。

## 按依赖顺序求解

1. 分别register host与bot-guest，保持各自token与连接。
2. 双端AUTH并等待PEER_JOINED再开始游戏，按协议推进与等待进度。
3. 满足时机后RunComplete，再经HTTP claim取结果。

## 结果与验证标准

原文结果 NepCTF{bcaff050dfd983a85c73ad969eded5fb6eea353117d582820c22ed182697bead}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

服务地址是历史实例；TooEarly需检查状态，不应无限重试同一不合法完成包。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/writeup.md](writeups/writeup.md)
