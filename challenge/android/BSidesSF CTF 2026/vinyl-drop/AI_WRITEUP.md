# vinyl-drop — AI 易理解版 Writeup

> 比赛：BSidesSF CTF 2026｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是构造被Firebase Cloud Function接受的收据QR。校验字段只有当前UID、购买金额和时间，客户端输入缺少不可伪造的购买凭据绑定。

## 材料与证据

- [writeups/solution/frida-validate.js](<writeups/solution/frida-validate.js>)
- [writeups/solution/README.md](<writeups/solution/README.md>)

## 推导与解题步骤

1. 阅读登录/注册流程取得当前Firebase User UID，注意UID不等于email或ID token。

2. 观察validateScanPayload的错误信息，恢复三个加号分隔字段：`<uid>+<amount>+<unix_timestamp>`。

3. 金额需>=100；时间为Unix秒并在服务允许的最近30天内，用当前有效实例时间，不复制历史QR。

4. 在正常认证和AppCheck上下文中提交该字符串，可扫描自制QR，也可参考frida-validate.js替换应用提交参数。直接HTTP请求还需要正确Auth/AppCheck/App ID，不能只发送字符串。

## 结果与验证

成功应收到success/reward并在RewardActivity显示flag。原文没有列最终flag值，因此本文不编造。

## 复现边界与易错点

现成Test QRs是历史时刻样本，过期后不能作为当前成功测试。仅改变客户端显示不代表后端接受；应保留实际Cloud Function响应。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
