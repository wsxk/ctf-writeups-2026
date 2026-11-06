# I Saw Our Time Pass — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：车联网｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是从CAN日志中重组ISO-TP ZIP，并从协议控制字段提取四层压缩包密码。负载中有大量假flag，真正内容在0x702的四重ZIP里。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第42—50页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 按CAN ID及ISO-TP会话重组First Frame和Consecutive Frame，保留长度与序号，剔除PCI字段及末尾填充；从0x702找出四层嵌套ZIP。

2. 密码1：读取0x708 Flow Control的Block Size，按数值转ASCII，得到`FL0W_C0N7R0L_C4RR135_M34N1N6`。

3. 密码2：读取0x709的STmin原始字段值转ASCII，得到`53P4R4710N_71M3_15_4_CLU3`。

4. 密码3：读取0x702各First Frame声明长度，减256后转ASCII，得到`F1R57_FR4M3_KN0W5_M0R3`。

5. 密码4：收集0x703每段最后一个Consecutive Frame序号，每个序号是一个4位nibble，按顺序两两合成字节，得到`UD5_0V3R_1507P_H45_53CR375`。

6. 用四个密码逐层解包；密码提示文本不是flag，应读最终flag.txt。

## 结果与验证

官方第50页给出 `FLAG{C4N_BU5_WH15P3R3R_W45_H3R3}`。验证ZIP结构/CRC、四层解包及最终文本，而非只搜索任意flag字符串。

## 复现边界与易错点

CAN ID在幻灯片中按十六进制书写；Block Size示例输出则是十进制。不能混用打印进制。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
