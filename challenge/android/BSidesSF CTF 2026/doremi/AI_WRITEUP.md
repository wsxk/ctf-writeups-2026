# doremi — AI 易理解版 Writeup

> 比赛：BSidesSF CTF 2026｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是读取藏在VectorDrawable中的紫色文字。默认紫色背景让flag与背景重合，绿色文字是干扰；正确音高仅改变背景颜色，不产生解密密钥。

## 材料与证据

- [writeups/solution/hook.js](<writeups/solution/hook.js>)
- [writeups/solution/solution.py](<writeups/solution/solution.py>)

## 推导与解题步骤

1. 检查FrameActivity中rightPitch分支，定位绿色背景#8DC63F。

2. 动态路线：在onCreate(Bundle)调用原方法后找到rootLayout，将背景设为ARGB FF8DC63F；rightPitch是局部变量，不能把它当字段直接赋值。

3. 静态路线：apktool解资源，从sonnet、cadence、lyra、aria、tempo对应VectorDrawable收集paths，保留viewport与层次并合并为SVG，再加绿色背景。

4. 按画面排列顺序读取紫色字符，绿色干扰与同色背景融合。

## 结果与验证

本地solved.png可读出 `CTF{sl1ceandd1c3th3m}`；这是对随writeup保存图片的视觉核对，不是本次运行APK产生的截图。

## 复现边界与易错点

README写arya.xml而solution.py实际使用aria；复现以APK资源名核实。solution.py会删除指定workdir/decoded并调用npx安装转换工具，先检查路径与依赖再执行。本次未运行该脚本。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
