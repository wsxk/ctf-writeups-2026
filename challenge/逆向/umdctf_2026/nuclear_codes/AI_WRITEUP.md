# nuclear_codes：AI 可读解题说明

## 任务与证据范围

- 比赛：UMDCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：replacement_readable.txt 的Deriving the Final Expression与Verifying the Solution。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

最终高精度比较要求abs(left)<约2^-4096。原文将left化为-N/((a-c)(2a-b)(a+b-c))，对a>b>c>0分母为正，因此求整数N=0即可。

## 按依赖顺序求解

1. 记录原文三次齐次多项式N与严格次序，避免以近似浮点误差当零。
2. 采用原文给出的三个大整数候选，用任意精度整数逐项验证N严格等于0及a>b>c。
3. 逐行送入原程序，确认进入flag.txt读取成功路径。

## 结果与验证标准

原文结果 UMDCTF{ok_i_got_the_nuclear_codes_now_where_do_i_enter_them????}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

原文没有完整解释如何求得大整数三元组，只提供验证证书；近似exp/log描述不能替代最终严格推导。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/replacement_readable.txt](writeups/replacement_readable.txt)
