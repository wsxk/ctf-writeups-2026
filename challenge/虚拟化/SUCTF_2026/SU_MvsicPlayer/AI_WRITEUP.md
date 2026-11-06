# SU_MvsicPlayer — AI 可读解题说明

- 比赛：SUCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

恢复ddd.su_mv_enc对应WAV文件，并计算题目要求的MD5。

真正路径在Electron native vm_encryptor.node；SVM4头后是64字节块的四轮Feistel/Speck混合，每块密钥由前一密文两半异或派生，非CBC。

## 证据与输入

- [writeups/exp/exp.py](writeups/exp/exp.py)
- [writeups/writeup/writeup.md](writeups/writeup/writeup.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 解开app.asar并从main.js→native-bridge→napi_register_module_v1定位加密入口，区分JS的SVE4备用算法与真实SVM4格式。
2. 核对WAV RIFF/fmt/data检查及16位PCM路径；用原文trace识别64字节块，将状态拆16个大端uint32、左右各8字。
3. 初始key=bytes(range(32))，DELTA=0x70336364；按exp.py扩展4轮key，倒序恢复Feistel前态，再撤销Speck pair（ALPHA=8、BETA=3）。
4. 去4字节SVM4头后逐64字节解密；下一key始终从本块原密文前32B XOR后32B得到，不可用恢复明文派生。
5. 校验并去PKCS#7填充，保留恢复WAV的全部原字节，检查RIFF长度与音频块，再计算MD5并封装SUCTF{md5(wav file)}。

## 验证标准与结果

本地exp/exp.py含加解密两方向，可用于回环和重加密比对；正确结果应重加密得到原SVM4主体，最终MD5对象为WAV而不是.su_mv封装，官方说明已划去旧格式。

## 限制与易错点

exp以当前目录读取ddd.su_mv_enc并写ddd.wav，使用前需明确目录。播放器关闭会归档并删原文件，文档分析无需启动它。本文未计算MD5，也未声称已恢复音频。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
