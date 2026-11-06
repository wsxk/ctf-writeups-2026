# ufo — AI 易理解版 Writeup

> 比赛：SekaiCTF 2026｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是激活五种功能留下的ambient_trace bitmask，显露隐藏二维码并恢复缺失的QR结构。修改会员状态与本题数据流无关。

## 材料与证据

- [writeups/writeup.txt](<writeups/writeup.txt>)

## 推导与解题步骤

1. 在混淆类b7.w定位ambient_trace，在b7.a追踪更新：PdfSignature=1、PdfMetadata=2、OfficeText=4、Spreadsheet=8、ImageTransform=16。

2. 通过实际功能操作累计到31，或参考原文hook r7.m0.g(int,int,y0.k)，将第一个参数设31；也可编辑DataStore的ufo_prefs.preferences_pb，但需遵守protobuf格式。

3. 保留主屏出现的彩色像素，按原图网格确定每个module，去背景时不能凭空补造数据模块。

4. 二维码缺三个定位图形；用QR编辑器重建功能模块，按原文纠错等级L、mask5恢复格式信息，再解码。

## 结果与验证

原文读出clankedormiscgod，包装为 `SEKAI{clankedormiscgod}`。验证应来自二维码解码器可重复输出，而非OCR猜单词。

## 复现边界与易错点

原文使用AI清理图像可能引入像素变化，复现建议以原截图逐模块校验；代码与类名仅针对题目APK版本。本次没有修改用户DataStore。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
