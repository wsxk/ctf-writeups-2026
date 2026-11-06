# I_HATE_THIS_APP_REVENGE — AI 易理解版 Writeup

> 比赛：LYKNCTF｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

实际平台是Windows Tauri/Rust PE。目标是恢复AES-256-CTR加密图片中的角色名；关键是嵌入默认key与非连续的IV布局。

## 材料与证据

- [writeups/1_writeup.txt](<writeups/1_writeup.txt>)

本题在合集中的定位：LYKN合集第7节 I HATE THIS APP REVENGE。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 定位FIXED_ENCRYPTION_KEY字符串及getenv分支。未设置环境变量时从140C5FE10复制32字节默认key，HEX为487d3374255e6e447735463f63576a2d58414821446a3841616b61443979394d。

2. 读取encrypted.bin前12字节：前8字节作counter block前8字节，中间插4个00，原文件8—11字节放末尾，构成16字节IV。

3. 样本前缀001122334455667700000007对应IV00112233445566770000000000000007；仅对file[12:]执行AES-256-CTR解密。

4. 检查JPEG头、可完整解码及526×684尺寸，再识别雪中的Alolan Vulpix，按题意格式填写名称。

## 结果与验证

原文记录 `LYKNCTF{alolanvulpix}`。只得到可读前几个字节不足以证明图片正确，需完整图像验证。

## 复现边界与易错点

该题并非Android APK；普通nonce12+counter4构造不适用。若比赛实例设置了环境变量则默认key可能不适用；本文依据原文样本。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
