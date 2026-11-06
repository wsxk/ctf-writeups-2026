# GODMODE_999：AI 可读解题说明

## 任务与证据范围

- 比赛：UIUCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：1_writeup.txt 的GODMODE//999独立章节。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

RankedFS必须回放到已发布checkpoint28，忽略后续未提交transaction404。文件hash虽用SHA IV却是自定义压缩；直接模拟固件可准确恢复文件、可逆RAID9回放VM与最终AEAD。

## 按依赖顺序求解

1. 选择校验有效generation9 superblock并按事务rollback重建committed root。
2. Unicorn映射ROM于0，调用原hash解文件并拦截file_read，采集13类VM操作。
3. 逆算三阶段并枚举commit/rollback，合并重叠48字节code，第四阶段达MMR999后打开achievement seal。

## 结果与验证标准

原文player code r0llb4ck_th3_un1v3rs3_4nd_qu3u3_f0r_LV999!!!n0w!；flag uiuctf{r0llb4ck_th3_un1v3rs3_4nd_qu3u3_4g41n}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

CRC字段不是标准CRC，hashlib.sha256也不等价；one_button_clear是未提交诱饵。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/1_writeup.txt](writeups/1_writeup.txt)
