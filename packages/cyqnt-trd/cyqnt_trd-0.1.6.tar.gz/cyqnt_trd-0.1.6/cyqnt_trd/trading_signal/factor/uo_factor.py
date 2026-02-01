"""
UO（终极震荡指标，Ultimate Oscillator）因子

基于UO指标的交易因子
"""

import pandas as pd
import numpy as np


def uo_factor(
    data_slice: 'pd.DataFrame',
    period1: int = 7,
    period2: int = 14,
    period3: int = 28,
    oversold: float = 30.0,
    overbought: float = 70.0
) -> float:
    """
    终极震荡指标（UO）因子
    
    当UO低于oversold时看多，高于overbought时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 period3+1 行数据
                   最后一行是当前数据点，前面 period3 行是历史数据
        period1: 第一个周期（默认7）
        period2: 第二个周期（默认14）
        period3: 第三个周期（默认28）
        oversold: 超卖阈值（默认30）
        overbought: 超买阈值（默认70）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足或中性）
    """
    if len(data_slice) < period3 + 1:
        return 0.0
    
    # 计算Buying Pressure (BP) 和 True Range (TR)
    bp_list = []
    tr_list = []
    
    for i in range(period3):
        if len(data_slice) < period3 - i + 1:
            return 0.0
        
        idx = -(period3 - i + 1)
        current_close = data_slice.iloc[idx]['close_price']
        current_low = data_slice.iloc[idx]['low_price']
        
        if idx == -1:
            prev_close = data_slice.iloc[-2]['close_price']
            current_high = data_slice.iloc[-1]['high_price']
        else:
            prev_close = data_slice.iloc[idx-1]['close_price']
            current_high = data_slice.iloc[idx]['high_price']
        
        # Buying Pressure = Close - min(Low, Previous Close)
        bp = current_close - min(current_low, prev_close)
        bp_list.append(bp)
        
        # True Range
        tr1 = current_high - current_low
        tr2 = abs(current_high - prev_close)
        tr3 = abs(current_low - prev_close)
        tr = max(tr1, tr2, tr3)
        tr_list.append(tr)
    
    # 计算三个周期的平均值
    bp1 = np.sum(bp_list[-period1:])
    tr1 = np.sum(tr_list[-period1:])
    avg1 = bp1 / tr1 if tr1 != 0 else 0.0
    
    bp2 = np.sum(bp_list[-period2:])
    tr2 = np.sum(tr_list[-period2:])
    avg2 = bp2 / tr2 if tr2 != 0 else 0.0
    
    bp3 = np.sum(bp_list[-period3:])
    tr3 = np.sum(tr_list[-period3:])
    avg3 = bp3 / tr3 if tr3 != 0 else 0.0
    
    # 计算UO（加权平均）
    uo = 100.0 * (4.0 * avg1 + 2.0 * avg2 + avg3) / 7.0
    
    # 根据UO值返回因子
    if uo < oversold:
        return 1.0  # 超卖，看多
    elif uo > overbought:
        return -1.0  # 超买，看空
    else:
        return 0.0  # 中性

