# AGL 1 — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是从 Automotive Grade Linux 镜像找出第一个 flag。线索来自串口登录画面的 5900/tcp 提示；启动脚本的 `-vnc :0` 表明 GUI 已通过 VNC 导出。flag 位于仪表盘图标本身，不需要破解系统口令。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第19—21页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 检查 run.sh 中内核、raw 磁盘及 `-vnc :0` 参数；确认图形输出映射到本机5900端口。

2. 在隔离的比赛镜像环境启动后，以 VNC 客户端查看桌面。Dashboard 图标下方直接包含文字，应放大读取而不是只搜索终端日志。

3. 离线交叉验证：从镜像取出 `/usr/share/icons/hicolor/scalable/dashboard.svg`，检查图标文字；这与VNC看到的结果应一致。

## 结果与验证

官方第21页记录 `FLAG{W3lc0m3_t0_AGL!}`。验证标准是 SVG 内容与 GUI 展示一致。

## 复现边界与易错点

原文提到镜像允许 root 空密码登录，这是本题镜像的配置，不能推广到任意 AGL。挂载分析宜使用只读副本。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
