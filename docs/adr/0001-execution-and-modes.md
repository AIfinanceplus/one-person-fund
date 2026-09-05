# ADR 0001：执行后端与运行模式边界

状态：已采用（v0.1a）

## 决策

v0.1a 使用仓库内的 `PaperBroker` 作为唯一权威模拟执行端。`DEMO`、`REPLAY`、`PAPER` 都只能创建虚拟订单；不存在 `LIVE` 路由。每个订单携带 `execution_mode`，重复 `client_order_id` 返回原订单和原成交。

`REPLAY` 只能读取带时间戳的 fixture；`PAPER` 只能读取显式声明 `market_data_confirmed=true` 且来源不是 fixture 的外部快照。没有合格行情时返回阻塞或拒绝，不回退到 demo 数据。

## 取舍与未完成试验

本仓库没有把 NautilusTrader 或真实券商 SDK 放入关键路径：当前验收目标是无付费 key、可重复、标准 Python 环境下的 v0.1a。NautilusTrader 接入试验、ETF 实时行情权限、duration 历史元数据和十个前向交易日观察属于 v0.1b 阻塞项，不能由固定曲线 fixture 代替。

## 证据

- `backend/execution/paper.py`：模式白名单、成交成本与订单/成交幂等。
- `backend/data/fixture_source.py`：DEMO/REPLAY 输入隔离。
- `backend/data/paper_source.py`：PAPER 来源与最少历史观测门槛。
- `backend/orchestration/scenarios.py`：缺失数据、风险超限和预算阻塞演示。
- CI 在无外部行情和无付费模型 key 的环境运行核心测试。

## 后续变更条件

只有在记录安装版本、许可证、两只 ETF 的订单/成交/撤单/重启/回放证据后，才可提交新的执行后端 ADR。新后端必须通过同一套 FundBench 并保持 `PaperBroker` 的模式和幂等边界。

