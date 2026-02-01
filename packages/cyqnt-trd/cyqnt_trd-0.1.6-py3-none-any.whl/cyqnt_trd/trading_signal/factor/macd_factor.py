"""
MACD（移动平均收敛散度）因子

基于MACD指标的交易因子
"""

import pandas as pd
import numpy as np


def _ema(data: np.ndarray, period: int) -> float:
    """计算指数移动平均"""
    if len(data) < period:
        return np.mean(data)
    
    # 使用最后period个值计算EMA
    alpha = 2.0 / (period + 1.0)
    ema = data[-period]
    
    for i in range(-period + 1, 0):
        ema = alpha * data[i] + (1 - alpha) * ema
    
    return ema


def macd_level_factor(
    data_slice: 'pd.DataFrame', 
    fast_period: int = 12, 
    slow_period: int = 26
) -> float:
    """
    MACD Level因子
    
    当MACD线在信号线上方时看多，在下方时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 slow_period+9 行数据
                   最后一行是当前数据点，前面 slow_period+8 行是历史数据
        fast_period: 快速EMA周期（默认12）
        slow_period: 慢速EMA周期（默认26）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足或中性）
    """
    # 需要足够的数据来计算MACD和信号线（信号线通常是9期EMA）
    signal_period = 9
    min_period = max(slow_period, fast_period) + signal_period
    
    if len(data_slice) < min_period + 1:
        return 0.0
    
    # 获取收盘价
    close_prices = data_slice['close_price'].values
    
    # 计算快速和慢速EMA
    fast_ema = _ema(close_prices, fast_period)
    slow_ema = _ema(close_prices, slow_period)
    
    # MACD线 = 快速EMA - 慢速EMA
    macd_line = fast_ema - slow_ema
    
    # 计算MACD历史值以计算信号线
    # 需要计算过去signal_period个时间点的MACD值
    macd_values = []
    for i in range(signal_period):
        # 计算第i个历史时间点的MACD值
        # 需要从当前时间点往前推i+1个周期
        lookback = i + 1
        if len(data_slice) < slow_period + lookback:
            return 0.0
        
        # 获取到第i个历史时间点的数据（不包括当前时间点）
        # 例如：i=0时，取data_slice[:-1]（不包括最后一行）
        #      i=1时，取data_slice[:-2]（不包括最后两行）
        close_subset = data_slice.iloc[:-(lookback)]['close_price'].values
        if len(close_subset) < slow_period:
            return 0.0
        
        fast_ema_val = _ema(close_subset, fast_period)
        slow_ema_val = _ema(close_subset, slow_period)
        macd_val = fast_ema_val - slow_ema_val
        macd_values.append(macd_val)
    
    # 计算信号线（MACD的EMA）
    if len(macd_values) < signal_period:
        return 0.0
    
    signal_line = _ema(np.array(macd_values), signal_period)
    
    # 根据MACD和信号线的关系返回因子
    if macd_line > signal_line:
        return 1.0  # MACD在信号线上方，看多
    elif macd_line < signal_line:
        return -1.0  # MACD在信号线下方，看空
    else:
        return 0.0  # 中性

