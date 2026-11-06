# ICX_Regulate — AI 可读解题说明

- 比赛：PwnSec CTF 2026
- 分类：虚拟化
- 分析方式：本地原文与代码静态分析；本次未执行题目、solver 或远程交互。
- 附件登记状态：已下载；具体文件以本题目录为准。

## 目标与结论

向合法portal请求移植kernel mark，绕过/flag读取权限。

GMI检查器跳过低字节为ff/00的某些分支目标，可将禁用OCTPACK藏在LDI立即数再跳入执行；该指令能传播来源mark而不改变请求数值。

## 证据与输入

- [writeups/1_README.md](writeups/1_README.md)

来源身份和采集说明见 [metadata.json](metadata.json)；附件见 [attachments](attachments/)。

## 分步推导与操作

1. 恢复23位ISA、GMI校验和及guest runtime地址；准备位于地址低字节ff的隐藏OCTPACK(0x52)，先证明镜像被接受而运行时确实执行该字。
2. 注册portal并制造成功终端响应，从metadata[5]计算(slot-1)%23，定位0x6ffc05+slot*8的kernel-marked zero；不要假定ring索引从0开始。
3. 用shadow context/metadata调用原read producer，构造合法5字段读请求，但只更新影子producer，使内核暂未消费。请求word0地址为0x6ffb00+(producer%23)*10。
4. POP保持mark，再用OCTPACK把marked zero写到word0第1字节；参数计数5的高字节本来为0，因此数值不变、来源mark改变。
5. 发布shadow metadata、fence并按原ABI敲doorbell；后接NOP避免异步中断把LDI立即数当恢复PC，最后等待响应并打印FLAGBUF。

## 验证标准与结果

原文报告 pwnsec{10f7636384e74c19}。本地Docker假flag仅验证读路径；有效验证需分别检查镜像验证、mark传播、请求认证与实际读取。

## 限制与易错点

README提到exploit.gmi、/tmp/sandbox_text.u32及多份工具，但本地writeups仅README，不能假定已具备最终镜像。ABI、guest例程地址与标记传播均须对应同一构建。

## AI 继续分析时的规则

将上面的机制作为本题分析摘要，以链接的原始资料核对完整代码与常量。复现时记录输入、环境、关键中间状态和实际输出；原作者报告的结果不等于本次运行结果。若附件版本、协议响应或中间状态不符，先定位差异，不要臆造缺失数据。
