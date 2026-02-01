"""
BBP（牛熊力量，Bull Bear Power）因子

基于BBP指标的交易因子
"""

import pandas as pd
import numpy as np


def _ema(data: np.ndarray, period: int) -> float:
    """计算指数移动平均"""
    if len(data) < period:
        return np.mean(data)
    
    alpha = 2.0 / (period + 1.0)
    ema = data[-period]
    
    for i in range(-period + 1, 0):
        ema = alpha * data[i] + (1 - alpha) * ema
    
    return ema


def bbp_factor(data_slice: 'pd.DataFrame', period: int = 13) -> float:
    """
    牛熊力量（BBP）因子
    
    当BBP为正值时看多，为负值时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 period+1 行数据
                   最后一行是当前数据点，前面 period 行是历史数据
        period: EMA计算周期（默认13）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足）
    """
    if len(data_slice) < period + 1:
        return 0.0
    
    # 获取收盘价
    close_prices = data_slice['close_price'].values
    
    # 计算EMA
    ema_value = _ema(close_prices, period)
    
    # 当前最高价和最低价
    current_high = data_slice.iloc[-1]['high_price']
    current_low = data_slice.iloc[-1]['low_price']
    
    # 计算牛熊力量
    # Bull Power = High - EMA
    # Bear Power = Low - EMA
    bull_power = current_high - ema_value
    bear_power = current_low - ema_value
    
    # BBP = Bull Power + Bear Power
    bbp = bull_power + bear_power
    
    # 根据BBP值返回因子
    if bbp > 0:
        return 1.0  # 正值，看多
    elif bbp < 0:
        return -1.0  # 负值，看空
    else:
        return 0.0  # 中性

