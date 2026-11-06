# No My Bank!：AI 可读解题说明

## 任务与证据范围

- 比赛：NCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：NCTF官方PDF第34–60页；共享sources/NCTF_2026_Official_Writeup_text.txt对应章节。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

Godot资源AES加密和DLL RC4仅是外层。DLL的TLS callback把看似TEA的函数hook到SMC解密代码，真实检查为换表/换位Base64再逐字符加密。

## 按依赖顺序求解

1. 从can't open encrypted pack directory引用恢复PCK key并解资源，定位WinPopupTreasury到DLL checker。
2. 以G00dLuck2U解DLL或从临时目录保留明文，追TLS对0x24A0重定向至0x2700。
3. 解出SMC，逆逐字节变换、交换Base64每组1/2与3/4、映射回标准表解码key，再做gift字符变换。

## 结果与验证标准

官方结果 NCTF{Y0u_d3s3rv3_th1s_g1ft_b1bd7c719cfc}。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

直接逆静态TEA是诱饵；动态加载器参数涉及std::string/SSO ABI。原PDF图像含额外定位信息。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/NCTF_2026_Official_Writeup.pdf](writeups/NCTF_2026_Official_Writeup.pdf)
- [官方 PDF 的既有文本提取（含其他题，按章节定位）](../../../sources/NCTF_2026_Official_Writeup_text.txt)
