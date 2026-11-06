# Pay For 2048：AI 可读解题说明

## 任务与证据范围

- 比赛：NCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：NCTF官方PDF第70–72页的完整Node脚本。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

Electron的license-service.js通过wasm-bridge调用key校验与flag解密。字串RUST/WASM/2048变leet后形成license，规范化digest必须等于0xFC97CA2F。

## 按依赖顺序求解

1. 解app.asar并追JS→WASM接口，重现customDigest的32位溢出。
2. 构造NCTF-RU57-W45M-2048并校验digest，再以verifyContext取得sessionToken。
3. 保留token，用maxTile=2048及对应board的unlockContext调用解密接口。

## 结果与验证标准

验证顺序是verifyResult.ok、有效sessionToken、unlock返回flag；不能只凭license格式判成功。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

游戏上下文和会话token是额外条件；本地源码require路径应相对解包根目录。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/NCTF_2026_Official_Writeup.pdf](writeups/NCTF_2026_Official_Writeup.pdf)
- [官方 PDF 的既有文本提取（含其他题，按章节定位）](../../../sources/NCTF_2026_Official_Writeup_text.txt)
