# Handoff

## 当前目标

v0.1a（M0–M6）已验证；后续只推进有真实数据证据的 v0.1b PAPER 观察。不要把 fixture 回放写成前向市场结果。

## 恢复命令

```bash
python -m backend.cli full-demo
python -m backend.cli replay --fixture data/fixtures/curve_demo.json
python -m backend.cli persistent-demo --db /tmp/rates-fund.sqlite3
python -m backend.cli scenario --scenario missing-data
python -m backend.cli scenario --scenario risk-limit
python -m backend.cli scenario --scenario budget-exhausted
python -m unittest discover -s tests -v
python -m backend.api
```

## 验收证据

- `full-demo`：5 个 Pod、Portfolio 提案、Risk/Compliance 审批、2 个 fill、Ledger、50/50 FundBench。
- `REPLAY`：fixture 快照 mode 为 `REPLAY`，生成的订单 execution mode 也为 `REPLAY`。
- `StateStore`：事件去重、任务 lease 过期恢复、持久 run 和 artifact 测试通过。
- 四个异常场景返回预期状态；预算场景没有调用外部模型。
- GitHub Actions：M3 已知通过 run `33946627040`；v0.1a 最终通过 run `33947982231`，包含 full-demo 与 replay smoke。

## 代码边界

- 规则风控、Compliance、执行、账本和恢复不能依赖 LLM 解释。
- `DEMO` 只用固定 fixture；`REPLAY` 只用有时间的历史输入；`PAPER` 需要 `market_data_confirmed=true`、非 fixture 来源和至少 20 条历史观测。
- Treasury/FRED 曲线是研究输入，不是 ETF bid/ask；SHY/IEF 简化配置不是严格 DV01-neutral 2s10s trade。
- 不新增 live broker、真实资金、公开部署、身份认证或自动发送报告，除非另有明确授权。

## v0.1b 前置条件

1. 记录 NautilusTrader 或其他执行端的安装、版本、许可证与窄型功能试验。
2. 得到可再分发或有权限的 ETF quote/bar、duration、公司行动和交易日历数据。
3. 生成真实来源 PAPER snapshot，先通过一次 run 和对账，再开始 10 个实际交易日观察。
