# AGL 5 — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是读取KUKSA Data Broker中的41个字符。VSS JSON仅定义信号名称，值由启动服务动态写入，因此grep配置文件无法直接拿到完整flag。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第33—40页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 读`/usr/share/vss/vss.json`，定位`Vehicle.ctf.flag5.c1`至c41及hint；hint指向`/usr/sbin/agl-vss-helper.py`。

2. 从helper取得CA路径`/etc/kuksa-val/CA.pem`与token路径`/etc/xdg/AGL/agl-vss-helper/agl-vss-helper.token`，按官方示例连接`grpcs://127.0.0.1:55555`。

3. 依次执行`getValue Vehicle.ctf.flag5.cN`，以数值N排序拼接1—41字符；不要使用字符串字典序。

4. 静态备选：沿agl-setup.service→/usr/bin/agl-setup→/usr/lib/libaglsetup.so，恢复其用全零AES-256-ECB密钥解密的setValue命令。

## 结果与验证

官方第39页展示 `FLAG{valu3s_l1ve_1ns1d3_d4t4br0k3r}`。应检查41个槽位的实际返回与长度字段，不凭flag外观判成功。

## 复现边界与易错点

运行中的值与schema定义分离；截图显示的flag字符可能与槽位总数不同，需保留完整值和服务返回作核对，不自行补字符。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
