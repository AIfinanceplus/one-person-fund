# One Person Fund — Rates Fund OS

Rates Fund OS 是面向一人利率基金的 paper-only 控制系统：14 个岗位、5 个策略 Pod、可追溯数据快照、确定性风控、幂等模拟执行、独立账本、九页面 Command Center 和冻结验收集成在一条可重放链路中。

## 当前状态

**M0–M6 的 v0.1a 离线组织闭环已完成并在 CI 验证。** `full-demo` 会运行全部 5 个 Pod，生成 Portfolio/Risk/Compliance/Orders/Ledger，并执行 50 个 FundBench 冻结案例（数据与时间 10、策略与组合 10、风险与政策 12、执行与账本 12、Agent 与预算 6）。

这不是 v0.1b 前向市场数据模拟盘：仓库没有 live broker，不声称盈利，也没有把 Treasury 收益率当成 ETF 成交价。PAPER 只有在提供带来源、可用时间和至少 20 个历史观测的外部快照时才会运行。

## Quick start

```bash
python -m backend.cli demo
python -m backend.cli full-demo
python -m backend.cli persistent-demo --db /tmp/rates-fund.sqlite3
python -m backend.cli replay --fixture data/fixtures/curve_demo.json
python -m backend.cli scenario --scenario missing-data
python -m backend.cli scenario --scenario risk-limit
python -m backend.cli scenario --scenario budget-exhausted
python -m unittest discover -s tests -v
python -m backend.api
```

打开 <http://127.0.0.1:8000> 可查看静态九页面工作台。API 使用 Python 标准库 HTTP server；核心 CI 只需 Python 和 `pydantic`。

## 运行模式

| 模式 | 输入 | 可以声称的结果 |
|---|---|---|
| `DEMO` | 固定 fixture | 工程链路与异常路径 |
| `REPLAY` | 带时间和来源的历史 fixture | 指定样本的历史回放 |
| `PAPER` | 明确确认来源的外部快照 | 前向虚拟运行；数据不足则阻塞 |

## 目录

```text
backend/contracts/       14 个岗位机器契约
backend/domain/          Pydantic 领域对象与模式
backend/data/            fixture、Treasury/FRED 解析器、PAPER 输入门禁
backend/strategies/      Curve RV 与四个研究 Pod
backend/portfolio/       提案与工具映射
backend/risk/            确定性限额检查
backend/compliance/      模式、授权和过期检查
backend/execution/       幂等 PaperBroker
backend/ledger/           事件驱动账本投影
backend/orchestration/   DEMO/REPLAY/PAPER、持久运行与场景
backend/state/            SQLite 运行、任务 lease、事件和 artifact
backend/evaluation/      50 案例 FundBench
frontend/                九页面静态 Command Center
docs/adr/                取舍与阻塞记录
tests/                   领域不变量、模式和故障测试
```

## 安全边界

模型只能解释和提出候选；数量、单位、审批、模式和执行由代码约束。缺失、过期、无效或预算不足会显式返回 `ABSTAIN`、`REJECTED` 或 `BLOCKED`，不会用 0 或假行情补齐。SHY/IEF 配置是简化的 ETF 表达，不能称为严格 DV01 中性的 2s10s 价差。

## 交接

真实验证记录在 [`docs/STATUS.md`](docs/STATUS.md) 和 [`docs/HANDOFF.md`](docs/HANDOFF.md)。执行后端边界见 [`docs/adr/0001-execution-and-modes.md`](docs/adr/0001-execution-and-modes.md)。外部实时行情、NautilusTrader 试验和 10 个前向交易日观察仍是明确的 v0.1b 阻塞项。
