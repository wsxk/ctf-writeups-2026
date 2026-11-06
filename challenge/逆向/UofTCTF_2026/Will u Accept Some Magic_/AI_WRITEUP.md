# Will u Accept Some Magic?：AI 可读解题说明

## 任务与证据范围

- 比赛：UofTCTF 2026；分类：逆向。
- 目标：根据题目给定程序或数据，恢复能够满足原始验证逻辑的输入、动作序列或 flag。
- 本文状态：依据本地原文/solver 的静态分析重写；本轮未运行题目程序、解题脚本或远程服务。
- 本题证据定位：writeups/solve/hook.js与index.js。
- 附件登记状态：已下载。原始附件和来源映射见 [README](README.md) 与 [metadata](metadata.json)。

## 核心机制与推导

Binaryen把所有i32.ne替换为同签名hook调用，Node日志记录不相等操作的两侧数值，但返回原比较结果，因此是观察器而非强制通过补丁。

## 按依赖顺序求解

1. 读取program.wasm，emitText并插入hook.i32.ne导入，再重新编译。
2. 用WASI环境实例化，hook对不等比较打印a/b并保持(a!==b)?1:0。
3. 根据实际输入与比较日志建立字符/常量关系，再回原WASM验证恢复输入。

## 结果与验证标准

当前收录的hook.js/index.js只提供插桩能力，没有展示完整约束恢复或最终flag。

验证时应把恢复的值送回题目原始判定逻辑，或独立重算完整校验值；仅出现 flag 形状的字符串不足以证明成功。本文所引原作者结果不等于本轮重新验证。

## 复现边界与容易出错处

initialize不会保证执行所有检查器入口；必须找清实际导出调用。对文本做正则替换也需验证只改真实指令。

所有地址、偏移、长度和常量仅对应原文所分析的附件版本。代码块中的历史远程地址不代表当前可用；原文提及而本目录没有收录的脚本不能当作已提供文件。先确认输入文件名、工作目录、运行时和外部依赖，再按步骤复现。

## 原始证据与代码

- [writeups/solve/hook.js](writeups/solve/hook.js)
- [writeups/solve/index.js](writeups/solve/index.js)
