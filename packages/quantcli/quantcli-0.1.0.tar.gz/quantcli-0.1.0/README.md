# QuantCLI

**QuantCLI** 是一款专注于**因子挖掘与回测**的命令行工具，为个人量化研究者提供轻量、高效、可复现的研究环境。

## 特性

- 简洁的命令行界面
- 多数据源支持 (AKShare)
- 因子计算与评估 (IC、分位数分析)
- 基于 Backtrader 的回测引擎
- 数据自动缓存

## 安装

```bash
pip install -e .
```

## 快速开始

```bash
# 查看帮助
quantcli --help

# 获取数据
quantcli data fetch 600519 --start 2020-01-01 --end 2024-01-01

# 运行因子
quantcli factor run -n momentum -e "(close / delay(close, 20)) - 1"

# 回测策略
quantcli backtest run -s ma_cross --start 2020-01-01

# 查看配置
quantcli config show
```

## 命令

| 命令 | 功能 |
|------|------|
| `quantcli data` | 数据获取与管理 |
| `quantcli factor` | 因子计算与评估 |
| `quantcli backtest` | 回测引擎 |
| `quantcli config` | 配置管理 |

## 文档

详见 [docs/product_design.md](docs/product_design.md) 和 [docs/cli_guide.md](docs/cli_guide.md)

## 许可证

MIT License
