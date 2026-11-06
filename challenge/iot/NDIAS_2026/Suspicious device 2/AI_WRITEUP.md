# Suspicious device 2 — AI 易理解版 Writeup

> 比赛：NDIAS Automotive/IoT CTF｜目录分类：iot｜分析日期：2026-11-06
> 依据本地资料改写；未运行题目程序、solver 或远程利用。文中输出均为原文记录，不能当作本次复现结果。

## 目标与核心机制

目标是利用上一题已有的命令执行能力，找到内部数据库中的第二阶段flag。需要先读拓扑与现成查询工具，不能假设公网可以直接访问DB。

## 材料与证据

- [writeups/NDIAS_official_explanations.pdf](<writeups/NDIAS_official_explanations.pdf>)

本题在合集中的定位：官方PDF第94—96页。仅使用本题章节，不能用其他章节的 flag 作为结果。

## 推导与解题步骤

1. 复用stage1的DEBUG_EXEC通道，查看/app/config/cloud-topology.json；官方配置指向iot-db:5432、数据库iot_cloud，同时存在SSH22。

2. 检查/app/tools/query_db.py及连接配置，确认通过环境变量QUERY传入查询字符串。

3. 先列information_schema.tables确定schema和flag表，避免把telemetry或maintenance_users误当flag来源。

4. 通过现成脚本执行`SELECT * FROM flag`并保存响应；查询在云容器内执行，因此能到达内部iot-db。

## 结果与验证

官方第96页给出flag表返回记录。成功标准是从目标DB的flag表读取值，不是只枚举出表名。

## 复现边界与易错点

依赖stage1环境和服务状态；凭据、库名及工具路径均属于题目镜像。本次没有执行远程命令或数据库查询。

附件登记状态：部分。文件清单与来源见 [本题 README](README.md)；关键原始代码保留在上述证据文件中。
