"""
Stochastic（随机指标）因子

基于Stochastic %K指标的交易因子
"""

import pandas as pd
import numpy as np


def stochastic_k_factor(
    data_slice: 'pd.DataFrame', 
    period: int = 14, 
    k_smooth: int = 3, 
    d_smooth: int = 3,
    oversold: float = 20.0, 
    overbought: float = 80.0
) -> float:
    """
    Stochastic %K因子
    
    当Stochastic %K低于oversold时看多，高于overbought时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 period+1 行数据
                   最后一行是当前数据点，前面 period 行是历史数据
        period: Stochastic计算周期（默认14）
        k_smooth: %K平滑周期（默认3）
        d_smooth: %D平滑周期（默认3，未使用但保留参数）
        oversold: 超卖阈值（默认20）
        overbought: 超买阈值（默认80）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足或中性）
    """
    if len(data_slice) < period + k_smooth:
        return 0.0
    
    # 计算Stochastic %K
    # 需要period+k_smooth行数据来计算平滑后的%K
    k_values = []
    for i in range(k_smooth):
        if len(data_slice) < period + i + 1:
            return 0.0
        
        # 获取最近period+1行数据（包括当前点）
        high_prices = data_slice.iloc[-period-i-1:]['high_price'].values
        low_prices = data_slice.iloc[-period-i-1:]['low_price'].values
        close_prices = data_slice.iloc[-period-i-1:]['close_price'].values
        
        # 计算最高价和最低价
        highest_high = np.max(high_prices)
        lowest_low = np.min(low_prices)
        
        # 当前收盘价
        current_close = close_prices[-1]
        
        # 计算%K
        if highest_high == lowest_low:
            k = 50.0  # 中性值
        else:
            k = 100.0 * (current_close - lowest_low) / (highest_high - lowest_low)
        
        k_values.append(k)
    
    # 平滑%K（简单移动平均）
    k_smoothed = np.mean(k_values)
    
    # 根据Stochastic %K值返回因子
    if k_smoothed < oversold:
        return 1.0  # 超卖，看多
    elif k_smoothed > overbought:
        return -1.0  # 超买，看空
    else:
        return 0.0  # 中性

