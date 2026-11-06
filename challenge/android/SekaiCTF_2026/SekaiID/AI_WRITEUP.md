# SekaiID — AI 易理解版 Writeup

> 比赛：SekaiCTF 2026｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是读取Verifier管理界面使用的/system/flag.txt。原文实际成功路径利用android:debuggable=true通过ADB run-as获得Verifier UID，无需完成文中猜测的复杂IPC链。

## 材料与证据

- [writeups/README.md](<writeups/README.md>)
- [writeups/artifacts/flag.txt](<writeups/artifacts/flag.txt>)
- [writeups/exploit/run.sh](<writeups/exploit/run.sh>)
- [writeups/handout/tls_proxy.py](<writeups/handout/tls_proxy.py>)

## 推导与解题步骤

1. 检查两APK manifest和Verifier classes6.dex，IssuerRecoveryProvider.DEFAULT_PATH指向/system/flag.txt；确认Verifier debuggable=true。

2. 在授权的赛事实例通过tls_proxy.py把TLS端点转为本地ADB通道；应用启动后核对package UID与flag文件owner。原文文件为0600、owner即Verifier UID。

3. 执行相当于`adb shell run-as com.sekai.verifier cat /system/flag.txt`的读取，由包UID而非shell UID访问文件。

4. 保存实际返回内容，并核对它与AdminDashboard读取的路径一致。

## 结果与验证

原文/本地artifacts/flag.txt记录 `SEKAI{welcome-to-the-conference!}`。完成证据是run-as读出目标文件，而不是任意启动隐藏Activity。

## 复现边界与易错点

原文关于intent劫持、provider和claimsTag的预期利用包含推测与缺失步骤，不应写为已证明链。run-as仍受设备策略/SELinux影响，不能保证任意debuggable包都可读任意/system文件；本题依赖特定owner与权限。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
