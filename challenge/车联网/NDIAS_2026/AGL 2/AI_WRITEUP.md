# AGL 2 — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是恢复同一AGL镜像里的第二个flag。Camera页面只是线索展示，实际信息在JPEG的EXIF User Comment字段中，以Base64编码。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第22—25页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 在Camera画面发现细小提示；GUI若旋转，可按第22页将weston.ini的`transform=rotate-90`改为rotate-0，仅为方便观察。

2. 从镜像提取 `/usr/share/applications/data/still-image.jpg`。官方分区起点为2048扇区，扇区512字节，因此文件系统偏移是1048576；也可用7-Zip读取镜像。

3. 放大图片得到“提取图片并分析”的提示，读取EXIF User Comment，将其中字符串Base64解码。

## 结果与验证

官方第25页给出 `FLAG{EXIF_c4n_h1d3_4nyth1ng}`。解码结果应包含flag2标识，不能把图中可见提示当flag。

## 复现边界与易错点

磁盘偏移属于该附件版本；不要对所有raw镜像硬套1048576。EXIF比像素内容更关键。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
