# helm-hell — AI 可读解题说明

- 比赛：LA CTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

恢复使Helm模板渲染结果为true的输入。

652KB辅助模板把Brainfuck的纸带、指针与递归循环映射为Go模板操作；字符期望值隐藏在计数与循环中。

## 证据与输入

- [writeups/community/README.md](writeups/community/README.md)
- [writeups/community/solve.py](writeups/community/solve.py)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 将$sea识别为纸带、$helm为指针、$provisions为输入、$logbook为位置、$cargo为输出，分别对应八种BF操作。
2. 化简add126再sub125等恒等算式，按递归调用恢复232个函数的循环结构；不要简单按源码行数计数指令。
3. 逐次输入读取处追踪期望单元的构造：循环乘法、循环后的增量和相减比较；恢复实际消费的输入长度与各字符约束。
4. 结合community/solve.py核对提取流程，再以候选进行helm template渲染并检查true。

## 验证标准与结果

原文给出 lactf{t4k1ng_7h3_h3lm_0f_h31m_73mp14t3s}；但标题自称LACTF 2025，目录为2026，且文中声称41次输入与候选长度需独立核对，结果不能直接视为当前附件已验证。

## 限制与易错点

这是社区材料的年份/长度疑点，须优先按附件模板和solver实际常量校正。不要部署Kubernetes，题目验证仅需模板渲染。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
