"""
CCI（商品通道指数）因子

基于CCI指标的交易因子
"""

import pandas as pd
import numpy as np


def cci_factor(
    data_slice: 'pd.DataFrame', 
    period: int = 20,
    oversold: float = -100.0, 
    overbought: float = 100.0
) -> float:
    """
    CCI因子
    
    当CCI低于oversold时看多，高于overbought时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 period+1 行数据
                   最后一行是当前数据点，前面 period 行是历史数据
        period: CCI计算周期（默认20）
        oversold: 超卖阈值（默认-100）
        overbought: 超买阈值（默认100）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足或中性）
    """
    if len(data_slice) < period + 1:
        return 0.0
    
    # 获取最近period+1行数据
    high_prices = data_slice.iloc[-period-1:]['high_price'].values
    low_prices = data_slice.iloc[-period-1:]['low_price'].values
    close_prices = data_slice.iloc[-period-1:]['close_price'].values
    
    # 计算典型价格 (TP = (High + Low + Close) / 3)
    tp = (high_prices + low_prices + close_prices) / 3.0
    
    # 当前典型价格
    current_tp = tp[-1]
    
    # 计算过去period期的典型价格移动平均
    sma_tp = np.mean(tp[:-1])
    
    # 计算平均偏差
    mean_deviation = np.mean(np.abs(tp[:-1] - sma_tp))
    
    # 计算CCI
    if mean_deviation == 0:
        cci = 0.0  # 中性值
    else:
        cci = (current_tp - sma_tp) / (0.015 * mean_deviation)
    
    # 根据CCI值返回因子
    if cci < oversold:
        return 1.0  # 超卖，看多
    elif cci > overbought:
        return -1.0  # 超买，看空
    else:
        return 0.0  # 中性

