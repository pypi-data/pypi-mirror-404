"""
ADX（平均趋向指数）因子

基于ADX指标的交易因子
"""

import pandas as pd
import numpy as np


def adx_factor(
    data_slice: 'pd.DataFrame', 
    period: int = 14,
    adx_threshold: float = 25.0
) -> float:
    """
    ADX因子
    
    当ADX高于阈值且+DI > -DI时看多，当ADX高于阈值且+DI < -DI时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 period*2+1 行数据
                   最后一行是当前数据点，前面 period*2 行是历史数据
        period: ADX计算周期（默认14）
        adx_threshold: ADX阈值，低于此值表示趋势较弱（默认25）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足或中性）
    """
    if len(data_slice) < period * 2 + 1:
        return 0.0
    
    # 计算True Range (TR)
    tr_list = []
    di_plus_list = []
    di_minus_list = []
    
    # 需要period+1行数据来计算DI
    for i in range(period):
        if len(data_slice) < period + 1 + i:
            return 0.0
        
        idx = -(period + 1 + i)
        if idx == -1:
            current_high = data_slice.iloc[-1]['high_price']
            current_low = data_slice.iloc[-1]['low_price']
            prev_close = data_slice.iloc[-2]['close_price']
        else:
            current_high = data_slice.iloc[idx]['high_price']
            current_low = data_slice.iloc[idx]['low_price']
            prev_close = data_slice.iloc[idx-1]['close_price']
        
        # True Range
        tr1 = current_high - current_low
        tr2 = abs(current_high - prev_close)
        tr3 = abs(current_low - prev_close)
        tr = max(tr1, tr2, tr3)
        tr_list.append(tr)
        
        # Directional Movement
        if idx == -1:
            prev_high = data_slice.iloc[-2]['high_price']
            prev_low = data_slice.iloc[-2]['low_price']
        else:
            prev_high = data_slice.iloc[idx-1]['high_price']
            prev_low = data_slice.iloc[idx-1]['low_price']
        
        plus_dm = current_high - prev_high if current_high > prev_high else 0.0
        minus_dm = prev_low - current_low if prev_low > current_low else 0.0
        
        # 如果plus_dm和minus_dm都大于0，取较大者，另一个设为0
        if plus_dm > minus_dm:
            minus_dm = 0.0
        elif minus_dm > plus_dm:
            plus_dm = 0.0
        else:
            plus_dm = 0.0
            minus_dm = 0.0
        
        # 计算DI
        if tr == 0:
            di_plus = 0.0
            di_minus = 0.0
        else:
            di_plus = 100.0 * plus_dm / tr
            di_minus = 100.0 * minus_dm / tr
        
        di_plus_list.append(di_plus)
        di_minus_list.append(di_minus)
    
    # 计算平滑后的TR、+DI和-DI（使用Wilder平滑）
    atr = np.mean(tr_list)  # 简化：使用简单平均，实际应该用Wilder平滑
    di_plus_smooth = np.mean(di_plus_list)
    di_minus_smooth = np.mean(di_minus_list)
    
    # 计算DX
    di_sum = di_plus_smooth + di_minus_smooth
    if di_sum == 0:
        dx = 0.0
    else:
        dx = 100.0 * abs(di_plus_smooth - di_minus_smooth) / di_sum
    
    # ADX是DX的移动平均（这里简化处理，实际应该用平滑的DX）
    adx = dx
    
    # 根据ADX和DI关系返回因子
    if adx < adx_threshold:
        return 0.0  # 趋势不明显，中性
    
    if di_plus_smooth > di_minus_smooth:
        return 1.0  # 上升趋势，看多
    elif di_minus_smooth > di_plus_smooth:
        return -1.0  # 下降趋势，看空
    else:
        return 0.0  # 中性

