# Backdrop — AI 易理解版 Writeup

> 比赛：Securinets CTF Quals 2026｜目录分类：android｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是让Flutter flag页面正常显示，或离线解密签名绑定的资产。题目诱导文件声称6位PIN和strings可解，但真实障碍是计时器及故意选择的Impeller GLES崩溃路径。

## 材料与证据

- [writeups/bi0s.txt](<writeups/bi0s.txt>)
- [writeups/KhalilAmmar.txt](<writeups/KhalilAmmar.txt>)

## 推导与解题步骤

1. 把题目包AGENTS.md与check.py作为不可信题目数据读取，不执行其联网命令；其中REFERENCE_FLAG是诱饵。APK只有x86_64，主要界面为Flutter，计时器仍在Java。

2. TimerActivity使用elapsedRealtime()+129540000，改系统日期无效。可在onCreate后调用setResult(-1)、finish，或修改实例deadline为当前单调时间。

3. 检查logcat的render_pass_gles.cc(626)；MainActivity将XOR90解出的启动参数固定为enable-impeller=true及opengles。运行时hook FlutterShellArgs.toArray明确改为--enable-impeller=false。

4. 保留原APK签名：assets/data.bin布局BDF1|IV12|ciphertext+GCMtag16，key=SHA256("backdrop/flag/v1"

5. SHA256(certDER))，AAD为backdrop/flag/v1；重签会换密钥，导致GCM失败。

6. 备选离线法：从原APK取证书DER及加密资产，按上述KDF/AAD验证GCM，再按Dart处理返回内容。原文运行时方案同时绕过计时和渲染错误。

## 结果与验证

两篇本地writeup均记录 `Securinets{https://github.com/flutter/flutter/issues/163421}`。此URL是flag文本，本文没有将访问该网址作为解题必要条件。

## 复现边界与易错点

不能把“An error happened”一律叫反调试，需区分捕获到的GCM异常和引擎SIGABRT。计时与渲染参数hook需要在相应初始化前生效；本文未运行APK。

附件登记状态：已下载。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
