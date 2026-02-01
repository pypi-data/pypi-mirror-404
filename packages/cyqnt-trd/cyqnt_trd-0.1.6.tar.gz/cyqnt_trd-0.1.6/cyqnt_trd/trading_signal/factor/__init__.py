"""
交易因子模块

定义各种交易因子，用于预测价格方向
因子函数签名: factor_func(data: pd.DataFrame, index: int) -> float
- 正数表示看多，负数表示看空，0表示中性
"""

# 导入所有因子
from .ma_factor import ma_factor, ma_cross_factor
from .rsi_factor import rsi_factor
from .stochastic_factor import stochastic_k_factor
from .cci_factor import cci_factor
from .adx_factor import adx_factor
from .ao_factor import ao_factor
from .momentum_factor import momentum_factor
from .macd_factor import macd_level_factor
from .stochastic_tsi_factor import stochastic_tsi_fast_factor
from .williams_r_factor import williams_r_factor
from .bbp_factor import bbp_factor
from .uo_factor import uo_factor
from .ema_factor import ema_factor, ema_cross_factor

__all__ = [
    'ma_factor',
    'ma_cross_factor',
    'rsi_factor',
    'stochastic_k_factor',
    'cci_factor',
    'adx_factor',
    'ao_factor',
    'momentum_factor',
    'macd_level_factor',
    'stochastic_tsi_fast_factor',
    'williams_r_factor',
    'bbp_factor',
    'uo_factor',
    'ema_factor',
    'ema_cross_factor',
]

