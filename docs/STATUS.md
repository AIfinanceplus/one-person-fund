# Status

## M0–M6：v0.1a 离线组织闭环 — verified

### 已完成

- 14 个岗位机器契约；5 个 Pod 均有可运行输出。Curve RV 是唯一可执行候选，Carry/Roll、Fed Path、Inflation、Macro Event 在缺少必需输入时明确 `ABSTAIN`。
- DEMO、REPLAY、PAPER 三种模式隔离；PAPER 强制非 fixture 来源、明确确认字段和至少 20 条历史曲线观测。
- 确定性 Risk/Compliance、long-only ETF 提案、幂等 PaperBroker、独立 Ledger、SQLite StateStore 与持久 demo。
- 九页面静态 Command Center：Command Center、Organization Graph、Strategy Map、Research Inbox、Portfolio、Risk Center、Trading Blotter、Decision Ledger、FundBench。
- 四种可验证场景：正常链路、缺失数据、风险超限、预算耗尽；重复事件/重启由 persistent demo 覆盖。
- FundBench 冻结集 50 案例：数据与时间 10、策略与组合 10、风险与政策 12、执行与账本 12、Agent 与预算 6。

### 本地验证（2026-09-05）

- `python -m unittest discover -s tests -v`：14 tests，全部通过。
- `python -m backend.cli full-demo`：`SUCCEEDED`；5 pods；Compliance `APPROVED`；FundBench `50/50`。
- `python -m backend.cli replay --fixture data/fixtures/curve_demo.json`：`REPLAY`，运行 ID `replay-fixture-curve-001`；订单 execution mode 为 `REPLAY`。
- 场景验证：`missing-data=ABSTAINED`、`risk-limit=REJECTED`、`budget-exhausted=BLOCKED`。
- API/UI smoke：`/api/full`、`/api/status`、`/api/strategy`、`/api/portfolio`、`/api/risk`、`/api/orders`、`/api/ledger`、`/api/fundbench`、`/api/demo`、`/api/roles` 均可读，首页包含 `Organization Graph`。

### GitHub 验证

- M3 基线：`3a19fd7606742d3385fb966d11c01195b6b0a85a`。
- M4 实现批次：`624e56dab14b4934c0f4de4193e2ecd0a53e235f`。
- CI 在加入 full/replay smoke 前的最终通过运行：`33946627040`。
- CI 已加入 Full organization 与 Replay smoke；等待本次提交的最新 run 结果后再把 run ID 固定到交接记录。

### 未完成 / 明确阻塞

- 尚未运行 NautilusTrader 接入试验；当前 `PaperBroker` 是窄型日频 ETF 模拟后端。
- 尚未取得并验证 ETF 实时价格、历史 duration、公司行动和交易日历数据，因此没有 v0.1b 前向 PAPER 观察，也不声称收益。
- API 仍是本地标准库 HTTP server；没有身份认证、公开部署、SSE 补拉或多进程生产部署。
- FundBench v1 的 50 案例是工程冻结集，不是策略 alpha 或盈利保证。

### 下一阶段（v0.1b）

1. 完成 NautilusTrader/执行后端 ADR 试验，或正式记录暂缓。
2. 接入有权限的 ETF quote/bar、duration、公司行动和日历源，生成带 provenance 的 PAPER snapshot。
3. 先做 1 次 forward PAPER run，再连续记录 10 个实际交易日的行情、风险、对账和异常恢复。

