# Tiny crackme — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：iot｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是恢复FLAG{30字符}输入。CTF任务的ECC相关哈希看似很强，但UART任务在每5字符处检查CRC32，泄露6个短块的约束，提供更小的搜索空间。

## 材料与证据

- [writeups/writeup.txt](<writeups/writeup.txt>)

## 推导与解题步骤

1. 从FreeRTOS任务创建点识别uart与ctf两个任务，沿UART调用链13270→10418→1128→5B7C→5A50→121A4定位CRC。

2. 实现反射CRC32，多项式EDB88320、初始FFFFFFFF、最终按位取反。六个目标是80B0CEE1、71F28109、F38B1F2F、FB2059C6、334BD5E1、8DD5DB45。

3. 在字母数字下划线字符集上建立4字节前向CRC状态表；枚举第5字节，从目标内部状态反推一步，与前向表匹配。

4. 每块保留所有候选并正向验CRC，再拼30字符；CRC有碰撞，最终还应经过完整ctf任务验证。

## 结果与验证

原文6块为L0W_L、4Y3R_、SK1LL、S_M4Y、_H3LP、S_Y0U，合成 `FLAG{L0W_L4Y3R_SK1LLS_M4Y_H3LPS_Y0U}`。

## 复现边界与易错点

原文dict只保留每个CRC状态的一个4字节候选，可能覆盖碰撞；若复现失败需保留候选列表。63^4约1575万条Python记录，内存不可忽略。本次未执行穷举或QEMU。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
