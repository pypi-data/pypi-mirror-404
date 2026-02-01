"""
AO（动量震荡指标，Awesome Oscillator）因子

基于AO指标的交易因子
"""

import pandas as pd
import numpy as np


def ao_factor(data_slice: 'pd.DataFrame') -> float:
    """
    AO（动量震荡指标）因子
    
    当AO为正值且上升时看多，为负值且下降时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 35 行数据（5+34）
                   最后一行是当前数据点，前面 34 行是历史数据
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足或中性）
    """
    # AO使用5期和34期的简单移动平均
    short_period = 5
    long_period = 34
    
    if len(data_slice) < long_period + 1:
        return 0.0
    
    # 计算中位数价格 (Median Price = (High + Low) / 2)
    median_prices = (data_slice['high_price'] + data_slice['low_price']) / 2.0
    
    # 计算短期和长期移动平均（不包括最后一行）
    short_ma = median_prices.iloc[-short_period-1:-1].mean()
    long_ma = median_prices.iloc[-long_period-1:-1].mean()
    
    # 当前AO值
    ao_current = short_ma - long_ma
    
    # 计算上一期的AO值（需要更多历史数据）
    if len(data_slice) < long_period + 2:
        # 如果数据不足，只根据当前AO值判断
        if ao_current > 0:
            return 1.0
        elif ao_current < 0:
            return -1.0
        else:
            return 0.0
    
    short_ma_prev = median_prices.iloc[-short_period-2:-2].mean()
    long_ma_prev = median_prices.iloc[-long_period-2:-2].mean()
    ao_prev = short_ma_prev - long_ma_prev
    
    # 判断趋势
    if ao_current > 0 and ao_current > ao_prev:
        return 1.0  # 正值且上升，看多
    elif ao_current < 0 and ao_current < ao_prev:
        return -1.0  # 负值且下降，看空
    elif ao_current > 0:
        return 0.5  # 正值但未上升，轻微看多
    elif ao_current < 0:
        return -0.5  # 负值但未下降，轻微看空
    else:
        return 0.0  # 中性

