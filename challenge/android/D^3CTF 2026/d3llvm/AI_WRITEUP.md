# d3llvm — AI 易理解版 Writeup

> 比赛：D^3CTF 2026｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是恢复64个十六进制字符组成的token，并重建手写模型生成的隐藏secret来解flag。通过nativeVerifyInput或把游戏分数改为100本身不足以得到正确AES密钥。

## 材料与证据

- [writeups/D3CTF-2026-Official-Writeup-CN.pdf](<writeups/D3CTF-2026-Official-Writeup-CN.pdf>)
- [writeups/D3CTF-2026-Official-Writeup-EN.pdf](<writeups/D3CTF-2026-Official-Writeup-EN.pdf>)
- [writeups/decrypt_model_emu.py](<writeups/decrypt_model_emu.py>)
- [writeups/emulate_payload.py](<writeups/emulate_payload.py>)
- [writeups/parse_mnn.py](<writeups/parse_mnn.py>)
- [writeups/README.md](<writeups/README.md>)
- [writeups/reveal_flag.py](<writeups/reveal_flag.py>)
- [writeups/reveal_remote.py](<writeups/reveal_remote.py>)
- [writeups/solve_angr.py](<writeups/solve_angr.py>)
- [writeups/solve_decrypt.py](<writeups/solve_decrypt.py>)
- [writeups/solve_z3.py](<writeups/solve_z3.py>)

## 推导与解题步骤

1. 从payload文件偏移52B0的D3SGN2结构读取text_off/size、nonce16、key32和明文SHA256；逐32字节异或SHA256(key|nonce|LE64(counter))，输出解密so并校验摘要ac4a4b6d774425ec553b3207607f4ab6f6052a72a893536e857eba8a91022f10。

2. 在解密payload基址+35330建立angr调用状态，第二参数为base+42FB8；16个16bit符号word按架构字节序写入，求返回x0=1，按每word四位HEX得到token。

3. 模型touch_model.mnn.enc用16字节key`This is 3DES`加4个NUL作AES-ECB解密，去PKCS7、跳12字节，再Base64解码。名称含3DES只是诱导。

4. MNN3.6优化后13个operation名逐一FNV1a64求和，每字符贡献4280720401113ED2；64位置激活后secret=A01C8100444FB480，不依赖实际笔画坐标。

5. FNV1a64(token)=C05F81BA6AC93CF5，再按README两个SplitMix64派生式组合secret、ROR47及常量，得到AES key=22032f61c4e8afd2d43b65e3b4528daa。

6. 对payload偏移4A94处48字节AES-ECB解密并严格校验PKCS7。

## 结果与验证

token=`196f0d201332b47deb98221f33c7f4a13d03de6c2a77279c4dbc1f87e4d297a8`；原文flag=`d3ctf{OLLVM_is_still_somewhat_useful_for_AI}`。逐层核验so摘要、checker返回、模型secret和padding。

## 复现边界与易错点

模型优化节点名可能随MNN版本/后端改变，不能用未优化图的名字直接代入。token长度是64个字符即32字节，不是64bit整数。原脚本简略unpad只截最后字节，复现应补完整填充验证。

附件登记状态：缺失。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
