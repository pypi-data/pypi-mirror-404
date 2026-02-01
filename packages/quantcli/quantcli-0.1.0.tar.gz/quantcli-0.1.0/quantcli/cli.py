"""QuantCLI 命令行界面

提供数据获取、因子计算、回测和配置管理命令。

Usage:
    quantcli --help
    quantcli data fetch --symbol 600519 --start 2020-01-01
    quantcli factor run -n momentum -e "(close / delay(close, 20)) - 1"
    quantcli backtest run -s dual_ma.py --start 2020-01-01
"""

import sys
from datetime import date, timedelta
from typing import Optional

import click
import pandas as pd
from tabulate import tabulate

from .core import DataManager, DataConfig, FactorEngine, BacktestEngine, BacktestConfig, Strategy
from .factors import FactorDefinition
from .utils import parse_date, format_date, today, get_logger, TimeContext

logger = get_logger(__name__)


# =============================================================================
# 通用选项
# =============================================================================

def verbose_option(f):
    """Verbose output option"""
    def callback(ctx, param, value):
        ctx.ensure_object(dict)
        ctx.obj["verbose"] = value
        if value:
            import logging
            logging.basicConfig(level=logging.DEBUG)
    return click.option("-v", "--verbose", is_flag=True, help="Enable verbose output", callback=callback)(f)


def date_type(s: str) -> date:
    """Click type for date validation"""
    try:
        return parse_date(s)
    except Exception:
        raise click.BadParameter(f"Invalid date: {s}. Use YYYY-MM-DD format")


# =============================================================================
# 主命令
# =============================================================================

@click.group()
@click.version_option(version="0.1.0", prog_name="quantcli")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output", default=False)
@click.pass_context
def quantcli(ctx, verbose):
    """QuantCLI - 量化因子挖掘与回测工具"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    logger.info(f"QuantCLI v0.1.0 started")


# =============================================================================
# Data 命令
# =============================================================================

@quantcli.group()
def data():
    """数据获取与管理"""
    pass


@data.command("fetch")
@click.argument("symbol", type=str)
@click.option("--start", type=date_type, required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end", type=date_type, default=None, help="End date (YYYY-MM-DD)")
@click.option("--source", type=click.Choice(["akshare", "baostock", "mixed"]), default="mixed", help="Data source")
@click.option("--use-cache/--no-cache", default=True, help="Use cache")
@click.option("--output", type=click.Path(), default=None, help="Output file path")
@click.pass_context
def data_fetch(ctx, symbol, start, end, source, use_cache, output):
    """获取股票日线数据"""
    if end is None:
        end = today()

    click.echo(f"Fetching {symbol} data from {format_date(start)} to {format_date(end)}...")

    config = DataConfig(source=source)
    dm = DataManager(config)

    try:
        df = dm.get_daily(symbol, start, end, use_cache=use_cache)

        if df.empty:
            click.echo(f"No data found for {symbol}")
            return

        click.echo(f"Retrieved {len(df)} rows")

        # 数据统计
        if "close" in df.columns:
            click.echo(f"Close: {df['close'].min():.2f} - {df['close'].max():.2f}")

        # 输出到文件
        if output:
            if output.endswith(".csv"):
                df.to_csv(output, index=False)
            elif output.endswith(".parquet"):
                df.to_parquet(output, index=False)
            else:
                df.to_csv(output, index=False)
            click.echo(f"Saved to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@data.group("cache")
@click.pass_context
def data_cache():
    """缓存管理"""
    pass


@data_cache.command("ls")
@click.pass_context
def data_cache_ls(ctx):
    """列出缓存文件"""
    config = DataConfig()
    dm = DataManager(config)
    sizes = dm.get_cache_size()

    if not sizes or "_total" not in sizes:
        click.echo("No cached data found")
        return

    rows = []
    for k, v in sizes.items():
        if k != "_total":
            rows.append([k, v])

    if rows:
        click.echo("Cached files:")
        click.echo(tabulate(rows, headers=["File", "Size"], tablefmt="simple"))
    else:
        click.echo("No cached files found")

    click.echo(f"\nTotal: {sizes.get('_total', '0')}")


@data_cache.command("clean")
@click.option("--older-than", type=int, default=None, help="Remove files older than N days")
@click.pass_context
def data_cache_clean(ctx, older_than):
    """清理缓存文件"""
    config = DataConfig()
    dm = DataManager(config)

    count = dm.clear_cache(older_than=older_than)
    click.echo(f"Cleaned {count} cache files")


@data.command("health")
@click.pass_context
def data_health(ctx):
    """检查数据源健康状态"""
    config = DataConfig()
    dm = DataManager(config)
    health = dm.health_check()

    click.echo("Data Manager Health:")
    for k, v in health.items():
        if k == "cache":
            continue
        click.echo(f"  {k}: {v}")


# =============================================================================
# Factor 命令
# =============================================================================

@quantcli.group()
def factor():
    """因子定义与计算"""
    pass


@factor.command("run")
@click.option("--name", "-n", required=True, help="Factor name")
@click.option("--expr", "-e", required=True, help="Factor expression/formula")
@click.option("--symbol", default="600519", help="Stock symbol for testing")
@click.option("--start", type=date_type, default="2020-01-01", help="Start date")
@click.option("--end", type=date_type, default=None, help="End date")
@click.option("--output", type=click.Path(), default=None, help="Output file path")
@click.pass_context
def factor_run(ctx, name, expr, symbol, start, end, output):
    """运行因子计算"""
    if end is None:
        end = today()

    click.echo(f"Computing factor '{name}'...")

    # 创建引擎
    config = DataConfig()
    dm = DataManager(config)
    engine = FactorEngine(dm)

    # 注册因子
    factor = FactorDefinition(name=name, type="technical", expr=expr)
    engine.register(factor)

    # 获取数据
    df = dm.get_daily(symbol, start, end)
    if df.empty:
        click.echo(f"No data for {symbol}")
        return

    # 添加 returns 列
    if "close" in df.columns:
        df = df.copy()
        df["returns"] = df["close"].pct_change()

    # 计算因子
    try:
        result = engine.compute(name, df)

        click.echo(f"Factor computed: {len(result)} values")
        if not result.empty:
            click.echo(f"  Mean: {result.mean():.4f}")
            click.echo(f"  Std: {result.std():.4f}")
            click.echo(f"  Min: {result.min():.4f}")
            click.echo(f"  Max: {result.max():.4f}")

        # 保存结果
        if output:
            result_df = result.reset_index()
            result_df.columns = ["date", name]
            result_df.to_csv(output, index=False)
            click.echo(f"Saved to {output}")

    except Exception as e:
        click.echo(f"Error computing factor: {e}", err=True)
        sys.exit(1)


@factor.command("eval")
@click.argument("name", type=str)
@click.option("--symbol", default="600519", help="Stock symbol")
@click.option("--start", type=date_type, default="2020-01-01", help="Start date")
@click.option("--end", type=date_type, default=None, help="End date")
@click.option("--method", type=click.Choice(["ic", "quantile", "full"]), default="ic", help="Evaluation method")
@click.pass_context
def factor_eval(ctx, name, symbol, start, end, method):
    """评估因子表现"""
    if end is None:
        end = today()

    click.echo(f"Evaluating factor '{name}'...")

    config = DataConfig()
    dm = DataManager(config)
    engine = FactorEngine(dm)

    df = dm.get_daily(symbol, start, end)
    if df.empty:
        click.echo(f"No data for {symbol}")
        return

    # 添加 returns 列
    df = df.copy()
    df["returns"] = df["close"].pct_change()

    try:
        if method == "ic":
            result = engine.evaluate_ic(name, df)
            click.echo(f"\nIC Analysis for {name}:")
            if "ic_stats" in result:
                stats = result["ic_stats"]
                click.echo(f"  IC Mean: {stats.get('ic_mean', 0):.4f}")
                click.echo(f"  IC Std: {stats.get('ic_std', 0):.4f}")
                click.echo(f"  IC IR: {stats.get('ic_ir', 0):.4f}")

        elif method == "quantile":
            result = engine.evaluate_quantiles(name, df)
            click.echo(f"\nQuantile Analysis for {name}:")
            click.echo(f"  Groups: {result.get('groups', 10)}")
            click.echo(f"  Long-Short Return: {result.get('long_short_return', 0):.4f}")

        elif method == "full":
            result = engine.evaluate_full(name, df)
            click.echo(f"\nFull Evaluation for {name}:")
            click.echo(f"  IC Mean: {result.ic_mean:.4f}")
            click.echo(f"  IC IR: {result.ic_ir:.4f}")
            click.echo(f"  Sample Size: {result.sample_size}")

    except Exception as e:
        click.echo(f"Error evaluating factor: {e}", err=True)
        sys.exit(1)


@factor.command("list")
@click.pass_context
def factor_list(ctx):
    """列出已注册的因子"""
    engine = FactorEngine()
    factors = engine.registry.list_all()

    if not factors:
        click.echo("No factors registered")
        return

    click.echo("Registered factors:")
    for name in factors:
        factor = engine.registry.get(name)
        if factor:
            click.echo(f"  - {name}: {factor.formula[:50]}...")


@factor.command("run-file")
@click.option("--file", "-f", required=True, type=click.Path(exists=True), help="Factor config YAML file")
@click.option("--symbol", default="600519", help="Stock symbol for testing")
@click.option("--start", type=date_type, default="2020-01-01", help="Start date")
@click.option("--end", type=date_type, default=None, help="End date")
@click.option("--output", type=click.Path(), default=None, help="Output file path")
@click.pass_context
def factor_run_file(ctx, file, symbol, start, end, output):
    """从 YAML 配置文件运行因子计算"""
    from .factors import load_strategy, FactorComputer

    if end is None:
        end = today()

    click.echo(f"Loading factor config from {file}...")

    try:
        config = load_strategy(file)
        click.echo(f"Config: {config.name} (v{config.version})")

        # 创建数据管理器
        config_data = DataConfig()
        dm = DataManager(config_data)

        # 获取数据
        df = dm.get_daily(symbol, start, end)
        if df.empty:
            click.echo(f"No data for {symbol}")
            return

        click.echo(f"Data: {len(df)} rows")

        # 获取权重配置中的因子
        weights = config.ranking.get("weights", {})
        from .factors.loader import load_all_factors
        factors = load_all_factors(weights, file)

        # 计算因子
        computer = FactorComputer()
        factor_data = computer.compute_all_factors(factors, {symbol: df}, {}, [symbol])

        # 显示结果
        click.echo("\nFactor Results:")
        if factor_data:
            for row in factor_data:
                for name, value in row.items():
                    if name != "symbol":
                        click.echo(f"  {name}: {value:.4f}" if isinstance(value, (int, float)) else f"  {name}: {value}")

        # 保存结果
        if output and factor_data:
            result_df = pd.DataFrame(factor_data)
            result_df.to_csv(output, index=False)
            click.echo(f"\nSaved to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@factor.command("score")
@click.option("--file", "-f", required=True, type=click.Path(exists=True), help="Factor config YAML file")
@click.option("--symbols", default=None, help="Stock symbols (comma-separated)")
@click.option("--start", type=date_type, default="2020-01-01", help="Start date")
@click.option("--end", type=date_type, default=None, help="End date")
@click.option("--top", type=int, default=None, help="Show top N results")
@click.option("--output", type=click.Path(), default=None, help="Output file path")
@click.pass_context
def factor_score(ctx, file, symbols, start, end, top, output):
    """根据 YAML 配置文件对股票进行评分选股"""
    from .factors import load_strategy, FactorPipeline

    if end is None:
        end = today()

    click.echo(f"Loading factor config from {file}...")

    try:
        config = load_strategy(file)
        click.echo(f"Config: {config.name} (v{config.version})")

        # 创建数据管理器
        config_data = DataConfig()
        dm = DataManager(config_data)

        # 解析股票列表
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(",")]
        else:
            symbol_list = ["600519"]

        click.echo(f"Fetching data for {len(symbol_list)} symbols...")

        # 获取多只股票数据
        stock_data = {}
        for symbol in symbol_list:
            df = dm.get_daily(symbol, start, end)
            if not df.empty:
                stock_data[symbol] = df

        if not stock_data:
            click.echo("No data found for any symbol")
            return

        click.echo(f"Got data for {len(stock_data)} symbols")

        # 使用 Pipeline 执行评分
        pipeline = FactorPipeline(file)
        results = pipeline.run(symbol_list, end, stock_data, pd.DataFrame(), limit=top)

        if results.empty:
            click.echo("No results")
            return

        # 显示结果
        click.echo("\n=== Scoring Results ===")
        click.echo(results.to_string(index=False))

        # 保存结果
        if output:
            results.to_csv(output, index=False)
            click.echo(f"\nSaved to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback
        if ctx.obj.get("verbose"):
            traceback.print_exc()
        sys.exit(1)


# =============================================================================
# Filter 命令
# =============================================================================

@quantcli.group()
def filter():
    """多阶段因子筛选"""
    pass


@filter.command("run")
@click.option("--file", "-f", required=True, type=click.Path(exists=True), help="Strategy config YAML file")
@click.option("--symbols", default=None, help="Stock symbols (comma-separated, default: all)")
@click.option("--start", type=date_type, default=None, help="Start date for price data (default: 60 days ago)")
@click.option("--end", type=date_type, default=None, help="End date for price data")
@click.option("--as-of", type=date_type, default=None, help="Time baseline date (for filtering as of this date)")
@click.option("--fundamental-date", type=date_type, default=None, help="Date for fundamental data")
@click.option("--top", type=int, default=None, help="Show top N results")
@click.option("--output", type=click.Path(), default=None, help="Output file path")
@click.option("--intraday/--no-intraday", default=True, help="Enable intraday data fetching")
@click.pass_context
def filter_run(ctx, file, symbols, start, end, as_of, fundamental_date, top, output, intraday):
    """运行多阶段因子筛选（基本面筛选 + 日线筛选 + 权重排序）"""
    from .factors.pipeline import FactorPipeline
    from .datasources import create_datasource

    # 设置时间基线
    if as_of is not None:
        TimeContext.set_date(as_of)
        click.echo(f"Time baseline set to: {format_date(as_of)}")

    if end is None:
        end = today()
    if start is None:
        start = end - timedelta(days=60)  # 默认最近60天
    if fundamental_date is None:
        fundamental_date = end

    click.echo(f"Loading strategy config from {file}...")

    try:
        pipeline = FactorPipeline(file)
        click.echo(f"Strategy: {pipeline.config.name} (v{pipeline.config.version})")

        # 检查是否为多阶段配置
        screening_config = pipeline.config.screening
        is_multi_stage = bool(screening_config.get("fundamental_conditions") or
                              screening_config.get("daily_conditions"))
        intraday_config = getattr(pipeline.config, 'intraday', {})
        has_intraday = bool(intraday_config.get("weights", {}))

        # 解析股票列表
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(",")]
        else:
            # 获取全部股票
            click.echo("Fetching all stock symbols...")
            source = create_datasource("mixed")
            stocks_df = source.get_stock_list()
            symbol_list = stocks_df["symbol"].tolist()
            click.echo(f"Found {len(symbol_list)} stocks")

        if not symbol_list:
            click.echo("No symbols to filter")
            return

        # ==================== 多阶段流程 ====================
        if is_multi_stage and intraday and has_intraday:
            # 完整多阶段流程：基本面 → 日线 → 分钟
            click.echo("Running multi-stage filtering...")

            # 阶段1: 基本面筛选
            click.echo(f"\n=== Stage 1: Fundamental Screening ===")
            click.echo(f"Fetching fundamental data for {len(symbol_list)} symbols...")
            source = create_datasource("mixed")
            fundamental_data = source.get_fundamental(symbol_list, fundamental_date)
            click.echo(f"Got fundamental data for {len(fundamental_data)} symbols")

            # 基本面条件筛选
            fundamental_conditions = screening_config.get("fundamental_conditions", [])
            candidates = pipeline.screening_only(symbol_list, fundamental_data) if fundamental_conditions else symbol_list
            if fundamental_conditions:
                click.echo(f"After fundamental screening: {len(candidates)}")

            if not candidates:
                click.echo("No candidates after fundamental screening")
                return

            # 阶段2: 日线筛选
            click.echo(f"\n=== Stage 2: Daily Screening ===")
            daily_conditions = screening_config.get("daily_conditions", [])
            if daily_conditions:
                # 只对候选获取日线数据
                click.echo(f"Fetching daily data for {len(candidates)} candidates...")
                dm = DataManager(DataConfig(source="mixed"))

                price_data = {}
                for symbol in candidates:
                    try:
                        df = dm.get_daily(symbol, start, end)
                        if not df.empty:
                            df = df.copy()
                            df["returns"] = df["close"].pct_change()
                            price_data[symbol] = df
                    except Exception as e:
                        logger.warning(f"Failed to get daily data for {symbol}: {e}")
                        continue

                click.echo(f"Got daily data for {len(price_data)} symbols")

                # 执行日线条件筛选
                if price_data and daily_conditions:
                    # 收集价格数据
                    candidate_price_data = []
                    for symbol in candidates:
                        if symbol in price_data:
                            df = price_data[symbol].copy()
                            df["symbol"] = symbol
                            candidate_price_data.append(df)

                    if candidate_price_data:
                        price_df = pd.concat(candidate_price_data, ignore_index=True)
                        latest_date = price_df["date"].max()
                        latest_df = price_df[price_df["date"] == latest_date].copy()

                        passed = pipeline._evaluate_screening(daily_conditions, latest_df)
                        candidates = [
                            s for s in candidates
                            if s in latest_df["symbol"].values and
                               passed.get(latest_df[latest_df["symbol"] == s].index[0], True)
                        ]
                        click.echo(f"After daily screening: {len(candidates)}")
            else:
                price_data = {}

            if not candidates:
                click.echo("No candidates after daily screening")
                return

            # 阶段3: 分钟级排名
            click.echo(f"\n=== Stage 3: Intraday Ranking ===")
            click.echo(f"Fetching intraday data for {len(candidates)} candidates...")
            source = create_datasource("mixed")

            intraday_data = {}
            for symbol in candidates:
                try:
                    df = source.get_intraday(symbol, start, end)
                    if not df.empty:
                        intraday_data[symbol] = df
                except Exception as e:
                    logger.warning(f"Failed to get intraday data for {symbol}: {e}")
                    continue

            click.echo(f"Got intraday data for {len(intraday_data)} symbols")

            # 执行分钟级排名
            results = pipeline.run_multi_stage(
                symbols=candidates,
                date=fundamental_date,
                price_data=price_data,
                intraday_data=intraday_data,
                fundamental_data=fundamental_data,
                limit=top
            )

        elif is_multi_stage:
            # 简化的多阶段：基本面 → 日线
            click.echo("Running simplified multi-stage filtering...")

            # 阶段1: 基本面
            click.echo(f"\n=== Stage 1: Fundamental Screening ===")
            click.echo(f"Fetching fundamental data for {len(symbol_list)} symbols...")
            source = create_datasource("mixed")
            fundamental_data = source.get_fundamental(symbol_list, fundamental_date)
            click.echo(f"Got fundamental data for {len(fundamental_data)} symbols")

            candidates = pipeline.screening_only(symbol_list, fundamental_data)
            click.echo(f"After fundamental screening: {len(candidates)}")

            if not candidates:
                click.echo("No candidates after fundamental screening")
                return

            # 阶段2: 日线
            click.echo(f"\n=== Stage 2: Daily Screening ===")
            click.echo(f"Fetching daily data for {len(candidates)} candidates...")
            dm = DataManager(DataConfig(source="mixed"))

            price_data = {}
            for symbol in candidates:
                try:
                    df = dm.get_daily(symbol, start, end)
                    if not df.empty:
                        df = df.copy()
                        df["returns"] = df["close"].pct_change()
                        price_data[symbol] = df
                except Exception as e:
                    logger.warning(f"Failed to get daily data for {symbol}: {e}")
                    continue

            click.echo(f"Got daily data for {len(price_data)} symbols")

            # 获取分钟数据（用于混合 ranking）
            click.echo(f"Fetching intraday data for {len(candidates)} candidates...")
            intraday_data = {}
            for symbol in candidates:
                try:
                    df = source.get_intraday(symbol, start, end)
                    if not df.empty:
                        intraday_data[symbol] = df
                except Exception as e:
                    logger.warning(f"Failed to get intraday data for {symbol}: {e}")
                    continue

            click.echo(f"Got intraday data for {len(intraday_data)} symbols")

            results = pipeline.run_multi_stage(
                symbols=candidates,
                date=fundamental_date,
                price_data=price_data,
                intraday_data=intraday_data,
                fundamental_data=fundamental_data,
                limit=top
            )

        else:
            # 原有单阶段流程
            click.echo("Running single-stage filtering...")

            click.echo(f"Fetching fundamental data for {len(symbol_list)} symbols...")
            source = create_datasource("mixed")
            fundamental_data = source.get_fundamental(symbol_list, fundamental_date)
            click.echo(f"Got fundamental data for {len(fundamental_data)} symbols")

            candidates = pipeline.screening_only(symbol_list, fundamental_data)
            click.echo(f"Candidates after screening: {len(candidates)}")

            if not candidates:
                click.echo("No candidates after screening")
                return

            click.echo(f"Fetching price data for {len(candidates)} candidates...")
            dm = DataManager(DataConfig(source="mixed"))

            price_data = {}
            for symbol in candidates:
                try:
                    df = dm.get_daily(symbol, start, end)
                    if not df.empty:
                        df = df.copy()
                        df["returns"] = df["close"].pct_change()
                        price_data[symbol] = df
                except Exception as e:
                    logger.warning(f"Failed to get data for {symbol}: {e}")
                    continue

            click.echo(f"Got price data for {len(price_data)} symbols")

            results = pipeline.run(
                symbols=candidates,
                date=fundamental_date,
                price_data=price_data,
                fundamental_data=fundamental_data,
                limit=top
            )

        if results.empty:
            click.echo("No results")
            return

        # 显示结果
        click.echo("\n=== Filter Results ===")
        click.echo(results.to_string(index=False))

        # 保存结果
        if output:
            results.to_csv(output, index=False)
            click.echo(f"\nSaved to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback
        if ctx.obj.get("verbose"):
            traceback.print_exc()
        sys.exit(1)
    finally:
        TimeContext.reset()


@filter.command("screening")
@click.option("--file", "-f", required=True, type=click.Path(exists=True), help="Strategy config YAML file")
@click.option("--symbols", default=None, help="Stock symbols (comma-separated)")
@click.option("--fundamental-date", type=date_type, default=None, help="Date for fundamental data")
@click.option("--output", type=click.Path(), default=None, help="Output file path")
@click.pass_context
def filter_screening(ctx, file, symbols, fundamental_date, output):
    """仅执行筛选阶段"""
    from .factors.pipeline import FactorPipeline
    from .datasources import create_datasource

    if fundamental_date is None:
        fundamental_date = today()

    click.echo(f"Loading strategy config from {file}...")

    try:
        pipeline = FactorPipeline(file)
        click.echo(f"Strategy: {pipeline.config.name}")

        # 解析股票列表
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(",")]
        else:
            source = create_datasource("mixed")
            stocks_df = source.get_stock_list()
            symbol_list = stocks_df["symbol"].tolist()

        # 获取基本面数据
        source = create_datasource("mixed")
        fundamental_data = source.get_fundamental(symbol_list, fundamental_date)

        # 执行筛选
        candidates = pipeline.screening_only(symbol_list, fundamental_data)

        click.echo(f"\nScreening Results: {len(candidates)} stocks passed")
        if candidates:
            click.echo(", ".join(candidates[:50]))
            if len(candidates) > 50:
                click.echo(f"... and {len(candidates) - 50} more")

        # 保存结果
        if output:
            with open(output, "w") as f:
                for s in candidates:
                    f.write(f"{s}\n")
            click.echo(f"\nSaved to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# =============================================================================
# Backtest 命令
# =============================================================================

@quantcli.group()
def backtest():
    """回测引擎"""
    pass


@backtest.command("run")
@click.option("--strategy", "-s", required=True, type=str, help="Strategy file or class name")
@click.option("--symbol", default="600519", help="Stock symbol")
@click.option("--start", type=date_type, default="2020-01-01", help="Start date")
@click.option("--end", type=date_type, default=None, help="End date")
@click.option("--as-of", type=date_type, default=None, help="Time baseline date (for backtesting as of this date)")
@click.option("--capital", type=float, default=1000000.0, help="Initial capital")
@click.option("--fee", type=float, default=0.0003, help="Transaction fee rate")
@click.pass_context
def backtest_run(ctx, strategy, symbol, start, end, as_of, capital, fee):
    """运行回测"""
    # 设置时间基线
    if as_of is not None:
        TimeContext.set_date(as_of)
        click.echo(f"Time baseline set to: {format_date(as_of)}")

    if end is None:
        end = today()

    click.echo(f"Running backtest for {symbol}...")

    # 加载策略
    try:
        strategy_cls = load_strategy(strategy)
    except Exception as e:
        click.echo(f"Error loading strategy: {e}", err=True)
        sys.exit(1)

    # 获取数据
    config = DataConfig()
    dm = DataManager(config)
    df = dm.get_daily(symbol, start, end)

    if df.empty:
        click.echo(f"No data for {symbol}")
        return

    click.echo(f"Data: {len(df)} rows")

    # 配置回测
    bt_config = BacktestConfig(
        initial_capital=capital,
        fee=fee,
        start_date=start,
        end_date=end
    )
    engine = BacktestEngine(bt_config)
    engine.add_data(symbol, df)

    # 运行回测
    try:
        result = engine.run(strategy_cls)

        click.echo(f"\n=== Backtest Results ===")
        click.echo(f"Total Return: {result.total_return:.2%}")
        click.echo(f"Annual Return: {result.annual_return:.2%}")
        click.echo(f"Max Drawdown: {result.max_drawdown:.2%}")
        click.echo(f"Sharpe Ratio: {result.sharpe:.2f}")
        click.echo(f"Sortino Ratio: {result.sortino:.2f}")
        click.echo(f"Win Rate: {result.win_rate:.2%}")
        click.echo(f"Total Trades: {result.total_trades}")

    except Exception as e:
        click.echo(f"Error running backtest: {e}", err=True)
        sys.exit(1)
    finally:
        TimeContext.reset()


@backtest.command("list")
@click.pass_context
def backtest_list(ctx):
    """列出历史回测结果"""
    click.echo("Historical backtests:")
    click.echo("(Not implemented yet)")


# =============================================================================
# Config 命令
# =============================================================================

@quantcli.group()
def config():
    """配置管理"""
    pass


@config.command("show")
@click.pass_context
def config_show(ctx):
    """显示当前配置"""
    config = DataConfig()
    click.echo("QuantCLI Configuration:")
    click.echo(f"  data.source: {config.source}")
    click.echo(f"  data.cache_dir: {config.cache_dir}")
    click.echo(f"  data.parallel: {config.parallel}")
    click.echo(f"  data.fillna: {config.fillna}")
    click.echo(f"  data.outlier_method: {config.outlier_method}")
    click.echo(f"  data.outlier_threshold: {config.outlier_threshold}")


@config.command("set")
@click.argument("key", type=str)
@click.argument("value", type=str)
@click.pass_context
def config_set(ctx, key, value):
    """设置配置项"""
    click.echo(f"Setting {key} = {value}")
    # TODO: 实现配置持久化
    click.echo("(Configuration persistence not implemented yet)")


# =============================================================================
# 辅助函数
# =============================================================================

def load_strategy(strategy_spec: str):
    """加载策略类

    Args:
        strategy_spec: 策略文件路径或类名

    Returns:
        Strategy 类
    """
    from pathlib import Path

    # 尝试作为文件加载
    strategy_path = Path(strategy_spec)
    if strategy_path.exists() and strategy_path.suffix == ".py":
        import importlib.util
        spec = importlib.util.spec_from_file_location("strategy", strategy_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 查找 Strategy 类
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, type) and attr.__name__ != "Strategy":
                # 找到继承自 object 的策略类 (非 Strategy 基类)
                if hasattr(attr, "__bases__") and Strategy in attr.__mro__[1:]:
                    return attr

        raise ValueError(f"No Strategy class found in {strategy_spec}")

    # 尝试作为内置策略名加载
    built_in_strategies = {
        "ma_cross": MaCrossStrategy,
    }

    if strategy_spec in built_in_strategies:
        return built_in_strategies[strategy_spec]

    raise ValueError(f"Unknown strategy: {strategy_spec}")


class MaCrossStrategy(Strategy):
    """简单均线交叉策略 (内置示例)"""

    name = "MA Cross"
    params = {"fast": 5, "slow": 20}

    def __init__(self):
        super().__init__()
        import backtrader as bt
        self.ma_fast = bt.indicators.SMA(self.data.close, period=self.params.fast)
        self.ma_slow = bt.indicators.SMA(self.data.close, period=self.params.slow)

    def next(self):
        if self.ma_fast[0] > self.ma_slow[0] and self.ma_fast[-1] <= self.ma_slow[-1]:
            self.buy()
        elif self.ma_fast[0] < self.ma_slow[0] and self.ma_fast[-1] >= self.ma_slow[-1]:
            self.sell()


# =============================================================================
# 入口点
# =============================================================================

def main():
    """CLI 入口点"""
    quantcli(obj={})


if __name__ == "__main__":
    main()
