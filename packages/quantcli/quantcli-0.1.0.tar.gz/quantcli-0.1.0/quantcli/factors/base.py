"""因子定义基础类"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class FactorType(str, Enum):
    """因子类型"""
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    INTRADAY = "intraday"
    COMPOSITE = "composite"


class FactorDirection(str, Enum):
    """因子方向"""
    POSITIVE = "positive"      # 值越高越好
    NEGATIVE = "negative"      # 值越低越好
    NEUTRAL = "neutral"        # 无方向性


@dataclass
class FactorDefinition:
    """因子定义

    Attributes:
        name: 因子名称
        type: 因子类型 (fundamental/technical)
        expr: 因子表达式
        direction: 因子方向 (positive/negative/neutral)
        description: 因子描述
        params: 可选参数
    """
    name: str
    type: str
    expr: str
    direction: str = "neutral"
    description: str = ""
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """验证参数"""
        if self.type not in [t.value for t in FactorType]:
            raise ValueError(f"Invalid factor type: {self.type}")
        if self.direction not in [d.value for d in FactorDirection]:
            raise ValueError(f"Invalid factor direction: {self.direction}")


@dataclass
class ScreeningStage:
    """筛选阶段配置

    Attributes:
        conditions: 简化的条件列表（向后兼容）
        fundamental_conditions: 基本面条件（需要基本面数据）
        daily_conditions: 日线条件（需要日线数据）
        limit: 候选数量限制
    """
    conditions: List[str] = field(default_factory=list)
    fundamental_conditions: List[str] = field(default_factory=list)
    daily_conditions: List[str] = field(default_factory=list)
    limit: int = 200

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScreeningStage":
        """从字典创建筛选阶段配置"""
        if isinstance(data, list):
            # 兼容旧格式：直接是条件列表
            return cls(conditions=data)
        return cls(
            conditions=data.get("conditions", []),
            fundamental_conditions=data.get("fundamental_conditions", []),
            daily_conditions=data.get("daily_conditions", []),
            limit=data.get("limit", 200),
        )


@dataclass
class IntradayStage:
    """分钟级阶段配置

    Attributes:
        weights: 因子权重配置
        normalize: 标准化方法
    """
    weights: Dict[str, float] = field(default_factory=dict)
    normalize: str = "zscore"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntradayStage":
        """从字典创建分钟级配置"""
        return cls(
            weights=data.get("weights", {}),
            normalize=data.get("normalize", "zscore"),
        )


@dataclass
class StrategyConfig:
    """策略配置

    Attributes:
        name: 策略名称
        version: 版本号
        screening: 筛选条件列表
        ranking: 权重配置
        intraday: 分钟级配置（可选）
        output: 输出配置
    """
    name: str
    version: str = "1.0.0"
    screening: Dict[str, Any] = field(default_factory=dict)
    ranking: Dict[str, Any] = field(default_factory=dict)
    intraday: Dict[str, Any] = field(default_factory=dict)
    output: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScreeningCondition:
    """筛选条件

    Attributes:
        expression: 表达式字符串，如 "pe < 50"
        column: 涉及的列名
    """
    expression: str
    column: str

    @classmethod
    def from_string(cls, expr: str) -> "ScreeningCondition":
        """从字符串解析筛选条件"""
        import re
        # 提取列名（简单的变量名匹配）
        match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*[<>=!]+', expr)
        if match:
            column = match.group(1)
        else:
            column = ""
        return cls(expression=expr, column=column)


@dataclass
class BonusCondition:
    """加分条件

    Attributes:
        condition: 条件表达式字符串，如 "volume_ratio < 0.8"
        weight: 加分权重
        description: 条件描述
    """
    condition: str
    weight: float
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BonusCondition":
        """从字典创建加分条件"""
        return cls(
            condition=data["condition"],
            weight=float(data["weight"]),
            description=data.get("description", "")
        )
