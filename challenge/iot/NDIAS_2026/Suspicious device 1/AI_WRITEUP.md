# Suspicious device 1 — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：iot｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是从SD卡中的ARM iot-agent恢复通信协议，发现残留DEBUG_EXEC命令。入口不是题面给出的云地址，而是固件中的连接逻辑与provision.bin配置。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第89—93页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 离线读取文件系统，检查/root/.ash_history与/usr/bin/iot-agent。原文以7-Zip探索镜像，并从配置/程序得出比赛云服务地址。

2. 追踪send_command/build_packet，识别IOT1帧：magic4、version1=01、command1=7F、flags/reserved各1、device_id16、length4、payload、CRC32。

3. 构造JSON payload的token及cmd字段；示例device_id为dev-7f3a91c2补NUL，debug token为dbg-9b7c4a1e-prod-only。CRC覆盖header+payload，length仅计payload。

4. 只在重建的比赛环境测试DEBUG_EXEC，通过服务器响应确认执行位置，再读取根目录flag_stage1.txt。

## 结果与验证

官方第93页展示成功返回flag_stage1.txt；本文不从低清截图猜录整串flag。应保存返回帧、状态和输出作验证。

## 复现边界与易错点

整数大小端须从build_packet汇编确认，幻灯片表格未完整规定；单靠该表不能声称完整可运行。远程地址为历史赛事端点，本次未连接。

附件登记状态：部分。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
