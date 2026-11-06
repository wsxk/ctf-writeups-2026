# stars_below — AI 可读解题说明

- 比赛：z0d1ak CTF Qualifiers
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

恢复route、callsign和自定义Base32 ticket，通过双VM终态检查。

导入重定位被洗牌并配合LD_BIND_NOT使PLT标签误导；真实算法为8!路线搜索、BLAKE2s派生、两个可逆ARX VM及短MAC。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 按每个PLT stub压入的重定位索引解析.rela.plt，重新标真实函数名；避免把伪strstr/SDL调用当作业务语义。
2. 枚举01234567的40320排列，复现32位route hash目标0xf06f770b，作者得到16403752；按AP9GLSEO索引得到PELAGOS9。
3. 按原文含终止NUL的domain separator派生name_hash和VM key；route参数是小端hash值0xf06f770b而非十进制16403752。
4. 解密并验证VM A，再将其程序hash纳入VM B key；从B目标倒退19轮，撤销桥b[i]=ROL(name_word[i],i+1)^a[perm[i]]，perm=[0,2,6,3,5,1,4,7]，再倒退A的24轮。
5. 每轮使用各自寄存器置换，得到8个小端u32的32B payload，附前4字节keyed BLAKE2s MAC，再以87RJF2ACZLVUMXB3D6GH9WNSYP5QK4ET编码58字符ticket。

## 验证标准与结果

作者报告 zdk{TH3_Lo4d3R_Dr34MS_IN_pA63_8ouNd4rIEs}。正向双VM、name guard及ticket MAC均需匹配，最后在--headless模式用三参数验证；自写正逆互逆不足以证明与原VM一致。

## 限制与易错点

本地只有README，引用solve_invariant.py/vm.py及分析blob未单独收录；需核对附件可提取情况。末字节Base32填充位和domain NUL容易出错，所有盐和调度常量必须从同一版本提取。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
