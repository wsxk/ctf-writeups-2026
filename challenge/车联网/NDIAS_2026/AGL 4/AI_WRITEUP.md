# AGL 4 — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是拼接分散在三个非主分区的flag片段。`/root/.hint.txt`提示可疑分区；各分区文件系统不同，单次strings或只看根分区会遗漏。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第29—32页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 读取隐藏提示并保留NUL字节的存在，使用十六进制查看可避免普通strings漏掉提示。

2. 枚举raw镜像分区。官方1.img为ext2，含flag4-part1.gif；2.img为SquashFS，含flag4-part2.zip，其内有文本片段。

3. 3.img为F2FS，需要支持F2FS的读取工具或只读挂载，提取flag4-part3.zip。

4. 按part1/3、part2/3、part3/3顺序拼接，不按文件枚举顺序猜测。

## 结果与验证

官方片段分别是 `FLAG{y0u_g0tta_b3`、`_susp1c10us_0f_un`、`us3d_p4rt1t10ns!}`；合并为 `FLAG{y0u_g0tta_b3_susp1c10us_0f_unus3d_p4rt1t10ns!}`。

## 复现边界与易错点

片段来自PDF截图，应以原始GIF/文本复核易混淆的0/O与1/l；本次没有实际挂载镜像。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
