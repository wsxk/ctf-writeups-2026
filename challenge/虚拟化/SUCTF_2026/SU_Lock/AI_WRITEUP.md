# SU_Lock — AI 可读解题说明

- 比赛：SUCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

从驱动VM提取加密参数和目标密文，逆解锁屏程序输入。

Rust安装载荷用RC4(SUCTF2026)解出用户态PE与驱动；IOCTL0x222004返回XXTEA变体参数，0x222008检查密文，驱动VM仅包装常量写出和相等判断。

## 证据与输入

- [writeups/exp/exp.py](writeups/exp/exp.py)
- [writeups/writeup/writeup.md](writeups/writeup/writeup.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 从安装包/运行期文件定位Locksetup.exe，沿RC4数据流离线解密嵌入PE和驱动；不需要在当前系统安装驱动。
2. 对g_VmCode_GetSecrets解析MOV_IMM32和STORE_OUT，得到delta=0x9e376a8e，key=[deadbeef,cafebabe,1337c0de,0badf00d]（十六进制）。
3. 对g_VmCode_Verify提取R2比较常量，按10个小端uint32组成40字节密文；注意脚本只是提取器，LOAD_IN/ASSERT_EQ分支仅打印，并未真正实现验证。
4. 按exp.py的btea_decrypt_variant撤销6+52//10=11轮，保留32位环绕，使用移位4/3/2/5的变体MX而非标准XXTEA库。
5. 将10个解密字小端序列化，核对UTF-8/填充，再正向重加密比对完整目标。

## 验证标准与结果

验证至少要求VM输出的5个参数一致和40字节正向密文完全相等；若再用原程序确认解锁，应使用隔离副本。脚本未硬编码最终flag，本次未运行输出。

## 限制与易错点

源码提取常量完整，但原文截图里的地址仍需匹配具体构建。不能仅看到解密字节可打印便认定成功；禁止把模拟VM读取常量的脚本描述为已完整模拟驱动。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
