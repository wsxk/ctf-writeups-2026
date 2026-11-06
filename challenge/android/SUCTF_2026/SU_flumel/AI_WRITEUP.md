# SU_flumel — AI 易理解版 Writeup

> 比赛：SUCTF 2026｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是逆Dart RC4 Warp→native AES-CBC校验链。Hermes bundle虽然执行了大量代码，但作者明确说明其自定义16字节算法未接入最终验证；bundle字节仍参与AES key/IV派生。

## 材料与证据

- [writeups/exp/exp.py](<writeups/exp/exp.py>)
- [writeups/writeup/SU_flumel Writeup.md](<writeups/writeup/SU_flumel Writeup.md>)

## 推导与解题步骤

1. 使用对应Dart VM3.11.1恢复ctfverify.dart逻辑，按数组异或(9*i+4B)得到RC4 key=TobeorNottobe；不要直接替换为标准RC4。

2. 定位qk9v，分清固定key0/iv0与runtime值：key0=youknowwhatImean，iv0=itsallintheflow!，各16字节。

3. 对cache.snap.bundle算FNV1a32与CRC32。key[i]=bundle[(11+17i)%n] xor ((fnv+i)&255) xor key0[i]；IV用(7+29i)%n及((crc>>8)+3i)&255。

4. 原文runtime key=9ae9908d89879e9981ca199e82cd1783，IV=dcd9c3d2daca55dca4af2aafa63aa3e9；以此AES-CBC解48字节target并严格去PKCS7。

5. 对解出的中间字节使用最终exp.py中的rc4warp_process相同密钥流再异或，因state演进不依赖输入明文，同过程可用于解密。

6. 完整正向做RC4 Warp→padding→AES-CBC，必须逐字节等于原48字节target。

## 结果与验证

原文结果 `SUCTF{w311_d0n3_y0u_kn0w_h3rm35_n0w}`。AES runtime值和最终密文是关键验证点。

## 复现边界与易错点

早期文章伪代码的t1/t2索引与最终exp.py的idx公式不同，应以对应附件真实逻辑核对，不混合两个版本；作者更换过附件。不要浪费上下文逐行分析44万行无关Hermes噪声。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
