"""
数据获取模块

提供从 Binance 获取期货和现货K线数据的功能，以及 Web3/链上 u-kline K 线数据，
以及带因子的 K 线获取（单点 / 时间区间 / 向前 n 点）。
"""

from .get_futures_data import get_and_save_futures_klines
from .get_trending_data import get_and_save_klines, get_and_save_klines_direct
from .get_web3_trending_data import get_and_save_web3_klines
from .get_kline_with_factor import (
    get_kline_with_factor_at_time,
    get_kline_with_factor_n_points,
    get_kline_with_factor_range,
)

__all__ = [
    'get_and_save_futures_klines',
    'get_and_save_klines',
    'get_and_save_klines_direct',
    'get_and_save_web3_klines',
    'get_kline_with_factor_at_time',
    'get_kline_with_factor_range',
    'get_kline_with_factor_n_points',
]

