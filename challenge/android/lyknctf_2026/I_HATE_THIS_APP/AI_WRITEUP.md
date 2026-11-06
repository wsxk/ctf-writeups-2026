# I_HATE_THIS_APP — AI 易理解版 Writeup

> 比赛：LYKNCTF｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目录归类为Android，但本地writeup明确描述Windows x64 Tauri/Rust PE。本题目标是识别防截图所调用的Windows API名称，非Android FLAG_SECURE。

## 材料与证据

- [writeups/1_writeup.txt](<writeups/1_writeup.txt>)

本题在合集中的定位：LYKN合集第6节 I HATE THIS APP。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 从RAR题目中确认PE格式，搜索capture protection日志和enable_capture_protection/disable_capture_protection命令。

2. 检查导入表，在user32.dll下找到SetWindowDisplayAffinity，不能只凭strings同名字符串作结论。

3. 交叉引用导入调用，原文wrapper地址14098C580，从对象+8取得HWND，启用时EDX=0x11，关闭为0。

4. 将0x11与本题防截图行为关联，提交底层API名称小写，而不是Tauri命令名或鼠标SetCapture函数。

## 结果与验证

原文结果 `LYKNCTF{setwindowdisplayaffinity}`。验证链是PE导入→实际调用→参数分支→题目行为。

## 复现边界与易错点

本题材料中同时包含另8道crack题，只有第6节相关。保留原目录但明确平台纠偏；本次未执行PE。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
