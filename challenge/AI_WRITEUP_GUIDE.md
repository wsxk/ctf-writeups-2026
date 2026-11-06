# AI 可读 Writeup 阅读说明

本次将目录内324道已登记题目的原始文章、作者说明和 solver 改写为独立的中文 `AI_WRITEUP.md`。2个重复目录提供规范题目跳转；5个尚无有效原解答的目录只提供待补说明。没有修改原始题目资料、附件或来源索引。

## 推荐读取流程

1. 在 [总索引](AI_WRITEUP_INDEX.md) 中按分类和题名定位，或读取 [JSON索引](AI_WRITEUP_INDEX.json) 做筛选。
2. 读取题目根目录 `AI_WRITEUP.md`，先确定输入、目标、核心机制、操作顺序及已知限制。
3. 需要精确常量、完整 payload 或协议交互时，打开文档链接的本地原文/solver。摘要不重复粘贴数百行数组、Base64二进制或整篇博客。
4. 对合集文章按题名定位章节；对PDF按文档标出的页码定位。对仅有solver的题目，以代码的实际数据流为依据。
5. 继续复现时逐步记录环境、输入、地址计算、中间状态、实际输出。只有与原程序一致的检查通过后，才把状态更新为运行验证成功。

## 如何理解证据

- **原文报告**：作者提供的flag、日志或成功陈述，本次没有独立运行验证。
- **静态分析**：从可读源码、solver和原文推导出的机制；与真实构建的一致性仍需复现检查。
- **资料缺口**：引用脚本未收录、步骤省略、编译载荷无源码、文章自相矛盾等；不会补造缺失内容。
- **局部成功**：解包、泄漏、任意读写、guest shell或通过一层检查，均需与最终题目目标区分。
- **来源冲突**：保留各来源结论及差异。自动提取的flag、类型名、算法名、长度、年份不因出现在原文中就自动可信。

全部文档都是本地分析改写，未执行题目二进制、利用脚本、设备操作或远程靶场交互。文档覆盖检查只证明文件和本地引用齐全，不证明算法、payload、远程服务或最终flag已运行成功。

## JSON 字段

| 字段 | 含义 |
|---|---|
| `directory` / `writeup` | 相对 `challenge` 的题目目录和新文档路径 |
| `canonical_directory` | 去重后的规范目录 |
| `rewrite_status` | `static_analysis` 静态改写；`source_limited` 明确资料不足；`duplicate` 重复入口；`pending_source` 原文待补 |
| `original_writeup_status` | 保留原目录登记值；不表示本次质量审查结论 |
| `original_attachment_status` | 原始附件收录状态；不保证运行依赖完整 |
| `mechanism` | 本题核心算法/漏洞及关键因果关系 |
| `evidence` | 相对题目目录的证据路径；其中可能包含 `../` 指向共享原文 |
| `limitations` | 缺口、环境依赖、来源矛盾或其他核验条件 |
| `executed` | 本次均为 `false` |
| `sha256` / `bytes` | 新文档的内容哈希和UTF-8字节数 |

`source_limited` 只标记部分明确不足的条目，不能用它反推其他题目材料已足够完整；每条的 `limitations` 才是具体依据。

## 维护

人工分析摘要保存在 `sources/ai_rewrite_*_summary.json`；生成器和对应逐题笔记位于 `scripts/` 与 `sources/`。总索引与覆盖报告可用 `python -X utf8 scripts/build_ai_writeup_index.py` 在 `challenge` 目录内重建。该命令只处理文档，不执行任何题目代码。

已有 `SHA256SUMS.txt` 对应原下载资料，本次新增文档的哈希在AI JSON索引中单独记录。
