"""
EMA（指数移动平均线）因子

基于EMA指标的交易因子
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


def ema_factor(data_slice: 'pd.DataFrame', period: int = 10) -> float:
    """
    EMA因子
    
    如果当前价格高于EMA，返回1（看多）
    否则返回-1（看空）
    
    Args:
        data_slice: 数据切片，必须包含至少 period+1 行数据
                   最后一行是当前数据点，前面 period 行是历史数据
        period: EMA周期（默认10，可选10/20/30/50/100/200）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足）
    """
    if len(data_slice) < period + 1:
        return 0.0
    
    # 获取收盘价
    close_prices = data_slice['close_price'].values
    
    # 计算EMA（不包括最后一行）
    ema = _ema(close_prices[:-1], period)
    
    # 当前价格
    current_price = data_slice.iloc[-1]['close_price']
    
    if current_price > ema:
        return 1.0  # 看多
    else:
        return -1.0  # 看空


def ema_cross_factor(
    data_slice: 'pd.DataFrame', 
    short_period: int = 10, 
    long_period: int = 20
) -> float:
    """
    EMA交叉因子
    
    当短期EMA上穿长期EMA时看多，下穿时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 long_period+2 行数据
                   最后一行是当前数据点，前面 long_period+1 行是历史数据
        short_period: 短期EMA周期（默认10）
        long_period: 长期EMA周期（默认20）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足）
    """
    if len(data_slice) < long_period + 2:
        return 0.0
    
    # 获取收盘价
    close_prices = data_slice['close_price'].values
    
    # 计算当前周期的EMA（不包括最后一行）
    short_ema_current = _ema(close_prices[:-1], short_period)
    long_ema_current = _ema(close_prices[:-1], long_period)
    
    # 计算上一周期的EMA（不包括最后两行）
    if len(data_slice) < long_period + 3:
        return 0.0
    
    short_ema_prev = _ema(close_prices[:-2], short_period)
    long_ema_prev = _ema(close_prices[:-2], long_period)
    
    # 上穿：之前短期EMA在长期EMA下方，现在在上方
    if short_ema_prev <= long_ema_prev and short_ema_current > long_ema_current:
        return 1.0  # 看多
    # 下穿：之前短期EMA在长期EMA上方，现在在下方
    elif short_ema_prev >= long_ema_prev and short_ema_current < long_ema_current:
        return -1.0  # 看空
    else:
        return 0.0  # 中性

