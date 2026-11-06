# Hook My Secret — AI 易理解版 Writeup

> 比赛：NCTF 2026｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是从NativeBridge的前缀相关输出恢复16字符stage2 key，再用数据库IV解stage3 AES。stage1图案解锁只影响界面流程，不参与最终密钥推导。

## 材料与证据

- [writeups/NCTF_2026_Official_Writeup.pdf](<writeups/NCTF_2026_Official_Writeup.pdf>)

本题在合集中的定位：NCTF官方PDF第72—75页；sources中有全册文字提取。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 用Frida取得NativeBridge.INSTANCE、ChallengeConfig.stage2TargetCipher，等Application初始化后再构造ChallengeStateManager。

2. 对比只改变第k字符的输入，其输出前k段保持不变，说明可以逐位置从左到右搜索，而非62^16全空间。

3. 对每位置枚举a-zA-Z0-9，以已确定prefix+candidate+若干A补齐16字符；调用encryptStage2，比较与目标的最长相同前缀。出现并列候选应保留并继续验证，不能无证据认为每轮唯一。

4. 完整16字符恢复后重新encryptStage2，必须与整个target一致；再记录stage2Key并通过stage状态。

5. DbHelper.getStage3Iv取得IV，ChallengeConfig.stage3CipherBase64解Base64；key经过trim及移除连字符后UTF8编码，调用AES/CBC/PKCS5Padding解密。

## 结果与验证

最终以完整stage2密文相等和stage3合法解密文本为证据。官方本节未写固定key、IV或flag，本文不把相邻VM Encryptor章节flag误归本题。

## 复现边界与易错点

本地官方PDF第72—75页含Frida脚本；复制PDF文本会夹杂页码、行号及控制字符，需清理。应核实密钥长度确为16字节和IV长度16。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
