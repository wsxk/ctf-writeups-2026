# SU_老年固件 — AI 易理解版 Writeup

> 比赛：SUCTF 2026｜目录分类：iot｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

现有writeup是分层固件提取分析记录，不是完整flag解答。可确认old.bin经单字节XOR7F后包含U-Boot风格头、XZ流与SMALLFW容器。

## 材料与证据

- [writeups/exp/old_firmware_extract.py](<writeups/exp/old_firmware_extract.py>)
- [writeups/writeup/writeup.md](<writeups/writeup/writeup.md>)

## 推导与解题步骤

1. 从attachment.zip取attachment/old.bin，逐字节异或0x7F，核对UBHDRv1、U-Boot1.1.3、Board:malta及baudrate=115200等字符串。

2. 在解码结果中定位XZ魔数FD377A585A00，原文顶层偏移2028、50ED4、51AA4。使用LZMADecompressor检查eof/unused_data，避免把多个流误当一个。

3. 后两个流展开为SMALLFW，进一步搜索内层XZ并解出ZIP；按ZIP条目读file_0_0.txt等样本文件。

4. 记录各层偏移、长度、文件名和校验，不因看到glibc字符串就宣称恢复出了程序源码树。

## 结果与验证

原文没有flag或判题成功证据。已完成部分仅是恢复容器与CTF_PAYLOAD样本文本；必须在后续找到真实题目校验逻辑才能补成完整解答。

## 复现边界与易错点

提取脚本默认attachment路径相对writeups层级可能不匹配，应显式传--attachment。ZIP成员写盘前还须规范化路径并限制在输出目录。本文没有运行原提取脚本。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
