# T.A.S P.W.N — AI 可读解题说明

- 比赛：NepCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：缺失；具体文件以本题目录为准。

## 目标与结论

重建演示影片，使指定模拟器中的游戏输入触发宿主计算器PoC。

原文复用bluescreen影片的guest链及XOR keystream，将184字节HIMITSU宿主body的调用目标改为WinExec(calc)，flag由主办验收签发。

## 证据与输入

- [writeups/writeup.md](writeups/writeup.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 固定BizHawk2.9.1、Mupen64Plus与日版ROM SHA1=B9CCA3FF260B9FF427D981626B82F96DE73586D3；缺少原始bk2影片不能单靠本文生成完整PoC。
2. 按原脚本parse_line/pack12解析55293至55343的51帧，重组612字节流；HOST_OFF=312、HOST_END=516，body偏移16、长184，魔数HIMITSU!。
3. 保留原resolver与guest解密链，以原body密文异或已知明文恢复keystream；逻辑x64字节先整体反转再按原keystream加密回填，避免把逻辑执行顺序当存储顺序。
4. 将WinExec与calc字符串及调用位移写入body，保留长度、头尾、控制器同步位；重新打包Input Log和bk2结构。

## 验证标准与结果

原文报告约55345帧出现计算器即通过演示，最终flag由主办签发。这里的成功条件是宿主可见PoC行为与环境一致，并非远程读flag；本次仅分析脚本，未播放影片。

## 限制与易错点

强依赖原影片、ROM版本、模拟器和keystream；不保证换版本可复现。原文完整代码含历史蓝屏payload作为恢复keystream的数据，应明确其用途而非运行它。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
