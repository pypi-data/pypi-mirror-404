"""
Momentum（动量指标）因子

基于动量指标的交易因子
"""

import pandas as pd
import numpy as np


def momentum_factor(data_slice: 'pd.DataFrame', period: int = 10) -> float:
    """
    动量指标因子
    
    当动量为正时看多，为负时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 period+1 行数据
                   最后一行是当前数据点，前面 period 行是历史数据
        period: 动量计算周期（默认10）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足）
    """
    if len(data_slice) < period + 1:
        return 0.0
    
    # 当前收盘价
    current_close = data_slice.iloc[-1]['close_price']
    
    # period期前的收盘价
    past_close = data_slice.iloc[-period-1]['close_price']
    
    # 计算动量
    momentum = current_close - past_close
    
    # 根据动量值返回因子
    if momentum > 0:
        return 1.0  # 正动量，看多
    elif momentum < 0:
        return -1.0  # 负动量，看空
    else:
        return 0.0  # 中性

