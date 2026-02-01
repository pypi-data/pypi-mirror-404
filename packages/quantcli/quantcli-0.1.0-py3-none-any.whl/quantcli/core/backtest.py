"""回测模块 - 基于 Backtrader

功能:
1. 回测引擎 (BacktestEngine)
2. 策略基类 (Strategy)
3. 回测结果 (BacktestResult)

Usage:
    >>> from quantcli.core import BacktestEngine, Strategy, BacktestConfig
    >>> from quantcli.core.data import DataManager
    >>> config = BacktestConfig(initial_capital=1000000, fee=0.0003)
    >>> engine = BacktestEngine(dm, config)
    >>> engine.add_data("600519", df)
    >>> result = engine.run(DualMAStrategy)
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Type, Union
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import numpy as np

import backtrader as bt
from backtrader import Strategy as BtStrategy

from ..utils import get_logger, parse_date, format_date
from ..datasources import create_datasource

logger = get_logger(__name__)


# =============================================================================
# 配置类
# =============================================================================

@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 1000000.0  # 初始资金
    fee: float = 0.0003                  # 手续费率
    slippage: float = 0.0005             # 滑点
    benchmark: str = "000300.SH"         # 基准指数
    start_date: Optional[Any] = None     # 开始日期
    end_date: Optional[Any] = None       # 结束日期
    timezone: str = "Asia/Shanghai"      # 时区


@dataclass
class Trade:
    """交易记录"""
    date: Any
    symbol: str
    side: str  # "buy" / "sell"
    price: float
    quantity: int
    fee: float
    pnl: Optional[float] = None


@dataclass
class BacktestResult:
    """回测结果

    Attributes:
        total_return: 总收益率
        annual_return: 年化收益率
        max_drawdown: 最大回撤
        sharpe: 夏普比率
        sortino: 索提诺比率
        win_rate: 胜率
        profit_factor: 盈亏比
        total_trades: 总交易次数
        trades: 交易记录 DataFrame
        equity_curve: 资金曲线 DataFrame
    """
    total_return: float = 0.0
    annual_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe: float = 0.0
    sortino: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    trades: pd.DataFrame = None
    equity_curve: pd.DataFrame = None
    benchmark_curve: pd.DataFrame = None

    def __post_init__(self):
        if self.trades is None:
            self.trades = pd.DataFrame()
        if self.equity_curve is None:
            self.equity_curve = pd.DataFrame()

    def to_dict(self) -> Dict:
        return {
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "max_drawdown": self.max_drawdown,
            "sharpe": self.sharpe,
            "sortino": self.sortino,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "total_trades": self.total_trades,
        }


# =============================================================================
# 数据源适配器
# =============================================================================

class PandasData(bt.feeds.PandasData):
    """Pandas 数据源适配器 - 将 DataFrame 转换为 Backtrader 格式"""

    params = (
        ("datetime", None),
        ("open", "open"),
        ("high", "high"),
        ("low", "low"),
        ("close", "close"),
        ("volume", "volume"),
        ("openinterest", -1),
    )


class MultiData(bt.feeds.PandasData):
    """多标的数据源"""

    params = (
        ("datetime", None),
        ("open", "open"),
        ("high", "high"),
        ("low", "low"),
        ("close", "close"),
        ("volume", "volume"),
    )


# =============================================================================
# 策略基类
# =============================================================================

class Strategy(BtStrategy):
    """策略基类 - 继承 Backtrader Strategy

    子类示例:
        >>> class DualMA(Strategy):
        >>>     name = "双均线策略"
        >>>     params = {"fast": 5, "slow": 20}
        >>>
        >>>     def __init__(self):
        >>>         super().__init__()
        >>>         self.ma_fast = bt.indicators.SMA(self.data.close, period=self.params.fast)
        >>>         self.ma_slow = bt.indicators.SMA(self.data.close, period=self.params.slow)
        >>>
        >>>     def next(self):
        >>>         if self.ma_fast[0] > self.ma_slow[0] and self.ma_fast[-1] <= self.ma_slow[-1]:
        >>>             self.buy()
        >>>         elif self.ma_fast[0] < self.ma_slow[0] and self.ma_fast[-1] >= self.ma_slow[-1]:
        >>>             self.sell()
    """

    name = "BaseStrategy"
    params = {}

    def __init__(self):
        super().__init__()
        # 订单记录
        self.order = None
        self.trade_log = []

        # 交易统计
        self.wins = 0
        self.losses = 0
        self.gross_profit = 0.0
        self.gross_loss = 0.0

    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.trade_log.append({
                    "date": self.datas[0].datetime.date(0),
                    "symbol": self.datas[0]._name,
                    "side": "buy",
                    "price": order.executed.price,
                    "quantity": order.executed.size,
                    "fee": order.executed.comm,
                })
            else:
                pnl = (order.executed.price - order.orders[0].created.price) * order.executed.size if len(self) > 1 else 0
                self.trade_log.append({
                    "date": self.datas[0].datetime.date(0),
                    "symbol": self.datas[0]._name,
                    "side": "sell",
                    "price": order.executed.price,
                    "quantity": order.executed.size,
                    "fee": order.executed.comm,
                    "pnl": pnl,
                })

                # 更新统计
                if pnl > 0:
                    self.wins += 1
                    self.gross_profit += pnl
                else:
                    self.losses += 1
                    self.gross_loss += abs(pnl)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            logger.warning(f"Order rejected: {order.status}")

        self.order = None

    def log(self, txt, dt=None):
        """日志输出"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f"{dt}: {txt}")

    def notify_trade(self, trade):
        """交易完成通知"""
        if trade.isclosed:
            logger.info(f"Trade: {trade.getdataname()} - PnL: {trade.pnl:.2f}")


# =============================================================================
# 回测引擎
# =============================================================================

class BacktestEngine:
    """回测引擎 - 封装 Cerebro

    Usage:
        >>> engine = BacktestEngine(dm, config)
        >>> engine.add_data("600519", df)  # df 包含 open/high/low/close/volume
        >>> result = engine.run(DualMAStrategy)
    """

    def __init__(
        self,
        config: Optional[BacktestConfig] = None
    ):
        """初始化回测引擎

        Args:
            config: 回测配置
        """
        self.config = config or BacktestConfig()
        self.cerebro = bt.Cerebro()

        # 设置资金
        self.cerebro.broker.setcash(self.config.initial_capital)

        # 设置手续费
        self.cerebro.broker.setcommission(commission=self.config.fee)

        # 设置滑点
        self.cerebro.broker.set_slippage_perc(self.config.slippage)

        # 分析器
        self.cerebro.addanalyzer(bt.analyzers.DrawDown)
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, riskfreerate=0.02, annualize=True)
        self.cerebro.addanalyzer(bt.analyzers.Returns)
        self.cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="time_return")

        # 交易记录
        self.cerebro.addobserver(bt.observers.Trades)

        # 数据源
        self._data_feeds: Dict[str, Any] = {}

    def add_data(
        self,
        symbol: str,
        df: pd.DataFrame,
        fromdate: Optional[Any] = None,
        todate: Optional[Any] = None
    ):
        """添加数据源

        Args:
            symbol: 股票代码
            df: DataFrame (必须包含: date, open, high, low, close, volume)
            fromdate: 开始日期
            todate: 结束日期
        """
        # 确保日期列
        df = df.copy()
        if "date" in df.columns:
            df["datetime"] = pd.to_datetime(df["date"])
            df.set_index("datetime", inplace=True)
        elif not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # 过滤日期
        if fromdate:
            df = df[df.index >= parse_date(fromdate)]
        if todate:
            df = df[df.index <= parse_date(todate)]

        # 创建数据源
        data = PandasData(dataname=df, datetime=None)
        data._name = symbol

        self.cerebro.adddata(data)
        self._data_feeds[symbol] = data

        logger.info(f"Added data: {symbol} ({len(df)} rows)")

    def add_data_from_datasource(
        self,
        symbol: str,
        dm: Any,
        start_date: Any,
        end_date: Any
    ):
        """从 DataManager 添加数据

        Args:
            symbol: 股票代码
            dm: DataManager 实例
            start_date: 开始日期
            end_date: 结束日期
        """
        df = dm.get_daily(symbol, start_date, end_date)
        if not df.empty:
            self.add_data(symbol, df, start_date, end_date)

    def run(
        self,
        strategy_cls: Type[Strategy],
        **strategy_params
    ) -> BacktestResult:
        """运行回测

        Args:
            strategy_cls: 策略类 (继承 Strategy)
            **strategy_params: 策略参数

        Returns:
            BacktestResult: 回测结果
        """
        # 添加策略
        self.cerebro.addstrategy(strategy_cls, **strategy_params)

        # 设置分析器
        if not self.cerebro.analyzers:
            self.cerebro.addanalyzer(bt.analyzers.DrawDown)
            self.cerebro.addanalyzer(bt.analyzers.SharpeRatio)

        # 运行回测
        results = self.cerebro.run()

        # 获取策略结果
        strategy_result = results[0]

        # 构建结果
        backtest_result = self._build_result(strategy_result)

        logger.info(f"Backtest finished: Return={backtest_result.total_return:.2%}, "
                    f"MaxDD={backtest_result.max_drawdown:.2%}, "
                    f"Sharpe={backtest_result.sharpe:.2f}")

        return backtest_result

    def _build_result(self, strategy_result: Strategy) -> BacktestResult:
        """构建回测结果"""
        # 获取分析器数据
        analyzers = strategy_result.analyzers

        # 最大回撤
        dd = analyzers.drawdown.get_analysis()
        max_drawdown = dd.get("max", {}).get("drawdown", 0) / 100 if dd else 0

        # 夏普比率
        sharpe = analyzers.sharperatio.get_analysis()
        sharpe_ratio = sharpe.get("sharperatio", 0)

        # 时间收益
        time_returns = analyzers.time_return.get_analysis()
        returns_series = pd.Series(time_returns)

        # 计算收益指标
        total_return = (1 + returns_series).prod() - 1 if len(returns_series) > 0 else 0

        # 年化收益率 (假设252交易日)
        n_years = len(returns_series) / 252
        annual_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0

        # 索提诺比率
        downside_returns = returns_series[returns_series < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino = (annual_return - 0.02) / downside_std if downside_std > 0 else 0

        # 交易统计
        trades_df = pd.DataFrame(strategy_result.trade_log)
        if not trades_df.empty:
            total_trades = len(trades_df)
            wins = (trades_df.get("pnl", 0) > 0).sum() if "pnl" in trades_df.columns else 0
            win_rate = wins / total_trades if total_trades > 0 else 0

            profit = trades_df[trades_df.get("pnl", 0) > 0]["pnl"].sum() if "pnl" in trades_df.columns else 0
            loss = abs(trades_df[trades_df.get("pnl", 0) < 0]["pnl"].sum()) if "pnl" in trades_df.columns else 1
            profit_factor = profit / loss if loss > 0 else 0
        else:
            total_trades = 0
            win_rate = 0
            profit_factor = 0

        # 资金曲线
        equity_curve = self._get_equity_curve(strategy_result)

        return BacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe=sharpe_ratio,
            sortino=sortino,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            trades=trades_df,
            equity_curve=equity_curve,
        )

    def _get_equity_curve(self, strategy_result: Strategy) -> pd.DataFrame:
        """获取资金曲线"""
        try:
            analyzer = strategy_result.analyzers.timers
            if hasattr(analyzer, "get_analysis"):
                data = analyzer.get_analysis()
                if data:
                    dates = [datetime.fromtimestamp(k / 1000) for k in data.keys()]
                    values = list(data.values())
                    return pd.DataFrame({
                        "date": dates,
                        "equity": values
                    }).set_index("date")
        except Exception as e:
            logger.debug(f"Could not get equity curve: {e}")

        # 备选方案: 使用 broker value
        try:
            values = []
            dates = []
            for i, data in enumerate(strategy_result.datas[0]):
                dates.append(strategy_result.datas[0].datetime.date(i))
                values.append(strategy_result.broker.getvalue())

            return pd.DataFrame({
                "date": dates,
                "equity": values
            }).set_index("date")
        except:
            pass

        return pd.DataFrame()

    def plot(self, **kwargs):
        """绘图

        Args:
            **kwargs: backtrader plot 参数
        """
        self.cerebro.plot(**kwargs)


# =============================================================================
# 便捷函数
# =============================================================================

def quick_backtest(
    symbol: str,
    df: pd.DataFrame,
    strategy_cls: Type[Strategy],
    initial_capital: float = 1000000.0,
    fee: float = 0.0003,
    **strategy_params
) -> BacktestResult:
    """快速回测 - 单行代码运行回测

    Args:
        symbol: 股票代码
        df: 数据 DataFrame
        strategy_cls: 策略类
        initial_capital: 初始资金
        fee: 手续费率
        **strategy_params: 策略参数

    Returns:
        BacktestResult
    """
    config = BacktestConfig(initial_capital=initial_capital, fee=fee)
    engine = BacktestEngine(config)
    engine.add_data(symbol, df)
    return engine.run(strategy_cls, **strategy_params)


def run_from_dm(
    dm: Any,
    symbol: str,
    strategy_cls: Type[Strategy],
    start_date: Any,
    end_date: Any,
    initial_capital: float = 1000000.0,
    fee: float = 0.0003,
    **strategy_params
) -> BacktestResult:
    """从 DataManager 运行回测

    Args:
        dm: DataManager 实例
        symbol: 股票代码
        strategy_cls: 策略类
        start_date: 开始日期
        end_date: 结束日期
        initial_capital: 初始资金
        fee: 手续费率
        **strategy_params: 策略参数
    """
    config = BacktestConfig(
        initial_capital=initial_capital,
        fee=fee,
        start_date=start_date,
        end_date=end_date
    )
    engine = BacktestEngine(config)
    engine.add_data_from_datasource(symbol, dm, start_date, end_date)
    return engine.run(strategy_cls, **strategy_params)
