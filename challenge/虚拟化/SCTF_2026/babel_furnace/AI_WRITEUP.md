# babel_furnace — AI 可读解题说明

- 比赛：SCTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

合并四层验证材料并逆转384位置换，恢复48字节flag。

Host、Python code object、bridge.pyd、Rust engine各持有部分share；单独分析engine会得到不完整opcode/立即数。组合后640条micro-op归约为6个uint64的14轮可逆变换。

## 证据与输入

- [writeups/exp/solve.py](writeups/exp/solve.py)
- [writeups/WP.md](writeups/WP.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 从Host的320个0x800片段按bootstrap key/tag/next链恢复模块，跟踪每片派生的新key并验证tag；Host API仍提供运行期share。
2. 从carrier的co_exceptiontable取80块token/immediate，co_linetable取16页key share，co_name取block permutation，co_qualname取bootstrap/input share。
3. 还原bridge的48字节长度检查、三方input permutation/mask及engine_resume状态机；遇到page/block请求时补齐packet字段并核对SplitMix64 packet tag。
4. 每页5块、每块8条；页key由四方share异或后派生，真实immediate同样合并四方。将640条micro-op与14轮高层算法对拍。
5. 从合并后的target倒序撤销word permutation、加法混合、nibble S-box、旋转和邻接XOR、round key，最后撤销input映射。

## 验证标准与结果

本地exp/solve.py提供实际恢复实现。验证标准是16页tag及80块状态一致、正向14轮回到target、48字节候选让Host输出Correct.；仅engine局部满足不足以证明完整链成功。

## 限制与易错点

不能遗漏Host share或把最多192次resume当192个VM块。脚本依赖的文件路径与模块提取必须先核对；原WP未直接写出最终flag，本次不从其他文本猜测。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
