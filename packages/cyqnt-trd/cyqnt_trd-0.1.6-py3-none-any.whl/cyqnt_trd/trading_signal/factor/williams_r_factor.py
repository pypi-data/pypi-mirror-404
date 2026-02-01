"""
Williams %R（威廉百分比变动）因子

基于Williams %R指标的交易因子
"""

import pandas as pd
import numpy as np


def williams_r_factor(
    data_slice: 'pd.DataFrame', 
    period: int = 14,
    oversold: float = -80.0, 
    overbought: float = -20.0
) -> float:
    """
    Williams %R因子
    
    当Williams %R低于oversold时看多，高于overbought时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 period+1 行数据
                   最后一行是当前数据点，前面 period 行是历史数据
        period: Williams %R计算周期（默认14）
        oversold: 超卖阈值（默认-80）
        overbought: 超买阈值（默认-20）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足或中性）
    """
    if len(data_slice) < period + 1:
        return 0.0
    
    # 获取最近period+1行数据
    high_prices = data_slice.iloc[-period-1:]['high_price'].values
    low_prices = data_slice.iloc[-period-1:]['low_price'].values
    close_prices = data_slice.iloc[-period-1:]['close_price'].values
    
    # 计算最高价和最低价（不包括当前行）
    highest_high = np.max(high_prices[:-1])
    lowest_low = np.min(low_prices[:-1])
    
    # 当前收盘价
    current_close = close_prices[-1]
    
    # 计算Williams %R
    if highest_high == lowest_low:
        williams_r = -50.0  # 中性值
    else:
        williams_r = -100.0 * (highest_high - current_close) / (highest_high - lowest_low)
    
    # 根据Williams %R值返回因子
    if williams_r < oversold:
        return 1.0  # 超卖，看多
    elif williams_r > overbought:
        return -1.0  # 超买，看空
    else:
        return 0.0  # 中性

