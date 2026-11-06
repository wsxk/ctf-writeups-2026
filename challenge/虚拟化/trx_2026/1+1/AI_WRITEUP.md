# 1+1 — AI 可读解题说明

- 比赛：TRX CTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

组合哈希分块候选与SPN逆变换，恢复128字节输入。

官方C程序对相邻哈希状态枚举4字节原像，Python脚本以固定seed重建S/P盒并逆SPN，再用可打印性筛选候选。

## 证据与输入

- [writeups/official_brute_fnv.c](writeups/official_brute_fnv.c)
- [writeups/official_solve.py](writeups/official_solve.py)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 读取official_brute_fnv.c的blocks数组，初始seed=0x0a1b2c3d，逐字节h=(h*0x01013255)^c，均为uint32；这与标准FNV-1a常量/顺序不同。
2. 每相邻blocks[i]→blocks[i+1]枚举四字节，保留所有碰撞候选。原C循环i<数组长度会在最后读越界，实际应仅处理长度减1个转移。
3. 按Python random.seed(0x1337)依次shuffle 256元素box、128元素pbox，box2[i]=box[box[i]]；随机调用顺序和版本行为必须匹配原表。
4. inv_spn先反转、异或0x67、查逆box2，撤销7次P置换，再逐字节减1并逆box，最后反转。对每块候选投影到明文，筛选可打印位置。
5. 对完整候选重新正向SPN及全部32段hash验证，不能仅使用replace(0xeb,空格)后的展示字符串作为flag。

## 验证标准与结果

源码仅打印逐步候选，无硬编码最终flag。正确标准是128字节原文正向生成全部32个目标状态；fnv_brute_res还包含编号32，但Python仅消费0–31，要隔离越界循环产生的无效候选。

## 限制与易错点

原文无完整文字WP；枚举2^32每块代价很高。Python按可打印性选择首个候选是启发式，需全局回代确认；C存在数组越界，不能原样当可靠验证器运行。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
