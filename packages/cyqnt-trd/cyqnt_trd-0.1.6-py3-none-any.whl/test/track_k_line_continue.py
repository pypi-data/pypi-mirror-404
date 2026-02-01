"""
实时跟踪K线，并显示最近3个周期的涨跌和涨跌幅度

使用方法：
    python track_k_line_continue.py --symbol BTCUSDT --interval 1m
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import Optional

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入实时价格跟踪器
try:
    from cyqnt_trd.online_trading.realtime_price_tracker import RealtimePriceTracker
except ImportError:
    # 如果导入失败，尝试从test_script导入
    try:
        from cyqnt_trd.test_script.realtime_price_tracker import RealtimePriceTracker
    except ImportError as e:
        print(f"导入错误: {e}")
        print("\n提示：请确保已安装 cyqnt_trd package 或项目路径正确")
        sys.exit(1)


def _parse_interval_minutes(interval: str) -> int:
    """
    解析时间间隔字符串，返回分钟数
    
    Args:
        interval: 时间间隔字符串，例如 '1m', '5m', '10m', '1h', '1d'
    
    Returns:
        对应的分钟数
    """
    interval_map = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "10m": 10,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "8h": 480,
        "12h": 720,
        "1d": 1440,
        "3d": 4320,
        "1w": 10080,
        "1M": 43200,  # 近似值
    }
    return interval_map.get(interval, 1)


def calculate_price_change(data_df, latest_kline: Optional[dict], interval: str, periods: int = 3) -> Optional[list]:
    """
    计算最近N个周期的涨跌和涨跌幅度（以当前时间为终点）
    
    Args:
        data_df: 包含K线数据的DataFrame
        latest_kline: 最新的K线数据（可能未完成）
        interval: 时间间隔，例如 '1m', '5m', '10m'
        periods: 要计算的周期数（默认3）
    
    Returns:
        包含每个周期涨跌信息的列表，每个元素为：
        {
            'period': 周期编号（1表示最近1个周期，2表示最近2个周期，以此类推）,
            'time': 时间字符串（周期开始时间 - 结束时间）,
            'open_price': 开盘价,
            'close_price': 收盘价,
            'change': 涨跌金额,
            'change_pct': 涨跌幅度（百分比）,
            'direction': '涨' 或 '跌'
        }
    """
    if data_df is None or len(data_df) == 0:
        return None
    
    from datetime import timedelta
    
    # 解析间隔分钟数
    interval_minutes = _parse_interval_minutes(interval)
    
    # 获取当前时间
    current_time = datetime.now()
    
    # 计算当前时间所在的K线周期开始时间（按标准时间边界对齐）
    # 例如10m周期：:00, :10, :20, :30, :40, :50
    current_minute = current_time.minute
    period_start_minute = (current_minute // interval_minutes) * interval_minutes
    current_period_start = current_time.replace(
        minute=period_start_minute,
        second=0,
        microsecond=0
    )
    current_period_end = current_period_start + timedelta(minutes=interval_minutes)
    
    results = []
    prev_close = None
    
    # 计算最近N个周期
    for i in range(periods):
        # 计算第i+1个周期的开始和结束时间
        period_start = current_period_start - timedelta(minutes=interval_minutes * i)
        period_end = period_start + timedelta(minutes=interval_minutes)
        
        # 如果是当前周期（i == 0），使用latest_kline（可能未完成）
        if i == 0 and latest_kline:
            period_data = {
                'open_time': int(period_start.timestamp() * 1000),
                'open_time_str': period_start.strftime('%Y-%m-%d %H:%M:%S'),
                'open_price': latest_kline['open_price'],
                'close_price': latest_kline['close_price'],
                'high_price': latest_kline['high_price'],
                'low_price': latest_kline['low_price'],
                'volume': latest_kline['volume'],
            }
        else:
            # 在data_df中查找对应的K线
            period_start_ms = int(period_start.timestamp() * 1000)
            period_end_ms = int(period_end.timestamp() * 1000)
            
            # 查找在周期时间范围内的K线（允许±60秒的容差，因为合并的K线可能有时间偏差）
            tolerance_ms = 60 * 1000  # 60秒容差
            matching_kline = data_df[
                (data_df['open_time'] >= period_start_ms - tolerance_ms) &
                (data_df['open_time'] <= period_start_ms + tolerance_ms) &
                (data_df['open_time'] < period_end_ms)
            ]
            
            if len(matching_kline) == 0:
                # 如果找不到，尝试找在周期结束时间之前，且最接近period_start的K线
                before_kline = data_df[data_df['open_time'] < period_end_ms]
                if len(before_kline) > 0:
                    # 计算每个K线与period_start的时间差
                    time_diff = (before_kline['open_time'] - period_start_ms).abs()
                    # 选择时间差最小的，但要求时间差不超过一个周期的一半（更宽松）
                    max_diff = interval_minutes * 60 * 1000 / 2
                    valid_kline = before_kline[time_diff <= max_diff]
                    if len(valid_kline) > 0:
                        closest_idx = time_diff[time_diff <= max_diff].idxmin()
                        matching_kline = valid_kline.loc[[closest_idx]]
                    else:
                        # 如果没有在合理范围内的，选择最接近的（但不超过一个周期）
                        max_diff_full = interval_minutes * 60 * 1000
                        valid_kline_full = before_kline[time_diff <= max_diff_full]
                        if len(valid_kline_full) > 0:
                            closest_idx = time_diff[time_diff <= max_diff_full].idxmin()
                            matching_kline = valid_kline_full.loc[[closest_idx]]
            
            if len(matching_kline) == 0:
                # 如果还是找不到，跳过这个周期
                # 打印调试信息以便排查
                print(f"⚠️  警告：无法找到周期 {i+1} 的K线数据 ({period_start.strftime('%H:%M')}-{period_end.strftime('%H:%M')})")
                continue
            
            period_data = {
                'open_time': matching_kline.iloc[0]['open_time'],
                'open_time_str': matching_kline.iloc[0]['open_time_str'],
                'open_price': matching_kline.iloc[0]['open_price'],
                'close_price': matching_kline.iloc[0]['close_price'],
                'high_price': matching_kline.iloc[0]['high_price'],
                'low_price': matching_kline.iloc[0]['low_price'],
                'volume': matching_kline.iloc[0]['volume'],
            }
        
        # 计算涨跌：每个周期都计算周期内的涨跌（收盘价 - 开盘价）
        change = period_data['close_price'] - period_data['open_price']
        change_pct = (change / period_data['open_price'] * 100) if period_data['open_price'] > 0 else 0
        
        # 格式化时间范围字符串
        # 对于当前周期（i==0），结束时间显示为当前时间
        if i == 0:
            time_range = f"{period_start.strftime('%H:%M')}-{current_time.strftime('%H:%M')}"
        else:
            time_range = f"{period_start.strftime('%H:%M')}-{period_end.strftime('%H:%M')}"
        
        results.append({
            'period': i + 1,  # 1表示最近1个周期
            'time': time_range,
            'open_price': period_data['open_price'],
            'close_price': period_data['close_price'],
            'change': change,
            'change_pct': change_pct,
            'direction': '涨' if change >= 0 else '跌'
        })
        
        # 更新prev_close为当前周期的收盘价
        prev_close = period_data['close_price']
    
    return results if results else None


def print_price_changes(kline_dict: dict, data_df, interval: str, periods: int = 3):
    """
    打印最近N个周期的涨跌信息
    
    Args:
        kline_dict: 最新K线数据字典
        data_df: 包含历史K线数据的DataFrame
        interval: 时间间隔，例如 '1m', '5m', '10m'
        periods: 要显示的周期数
    """
    print("\n" + "="*80)
    print(f"📊 K线实时跟踪 - {kline_dict['open_time_str']}")
    print("="*80)
    print(f"当前价格: {kline_dict['close_price']:.2f}")
    print(f"开盘价: {kline_dict['open_price']:.2f}")
    print(f"最高价: {kline_dict['high_price']:.2f}")
    print(f"最低价: {kline_dict['low_price']:.2f}")
    print(f"成交量: {kline_dict['volume']:.2f}")
    print("="*80)
    
    # 计算最近N个周期的涨跌（以当前时间为终点）
    price_changes = calculate_price_change(data_df, latest_kline=kline_dict, interval=interval, periods=periods)
    
    if price_changes:
        print(f"\n📈 最近{periods}个周期的涨跌情况:")
        print("-"*80)
        for change_info in price_changes:
            period_num = change_info['period']
            direction_emoji = "🟢" if change_info['direction'] == '涨' else "🔴"
            print(f"周期 #{period_num} ({change_info['time']}):")
            print(f"  开盘价: {change_info['open_price']:.2f}")
            print(f"  收盘价: {change_info['close_price']:.2f}")
            print(f"  涨跌: {direction_emoji} {change_info['direction']} {abs(change_info['change']):.2f} ({change_info['change_pct']:+.2f}%)")
            print()
    else:
        print(f"\n⚠️  数据不足，无法计算最近{periods}个周期的涨跌")
        print(f"   当前数据量: {len(data_df) if data_df is not None else 0} 条")
    
    print("="*80 + "\n")


async def track_klines(symbol: str, interval: str = "1m", periods: int = 3, ssl_verify: bool = False):
    """
    实时跟踪K线并显示涨跌信息
    
    Args:
        symbol: 交易对符号，例如 'BTCUSDT', 'ETHUSDT'
        interval: 时间间隔，例如 '1m', '5m', '1h'
        periods: 要显示的最近周期数（默认3）
        ssl_verify: 是否验证SSL证书（默认False，用于开发/测试）
    """
    # 创建实时价格跟踪器
    tracker = RealtimePriceTracker(
        symbol=symbol,
        interval=interval,
        lookback_periods=100,  # 保留最近100个周期的历史数据
        ssl_verify=ssl_verify,
        market_type="futures"
    )
    
    # 定义回调函数
    def on_new_kline(kline_dict, data_df):
        """新K线到来时的回调函数"""
        print_price_changes(kline_dict, data_df, interval=interval, periods=periods)
    
    # 注册回调函数
    tracker.register_on_new_kline(on_new_kline)
    
    print("="*80)
    print("🚀 实时K线跟踪已启动")
    print("="*80)
    print(f"交易对: {symbol}")
    print(f"时间间隔: {interval}")
    print(f"显示最近周期数: {periods}")
    print("="*80)
    print("\n等待新K线数据...\n")
    
    # 启动跟踪器（不运行 forever，而是手动控制）
    await tracker.start()
    
    # 定义定时打印任务
    async def periodic_print():
        """每分钟打印一次当前状态"""
        while tracker.is_running:
            await asyncio.sleep(60*5)  # 等待60秒
            if not tracker.is_running:
                break
            
            # 获取最新数据
            latest_kline = tracker.latest_kline
            data_df = tracker.get_data()
            
            if latest_kline and data_df is not None and len(data_df) > 0:
                # 使用最新K线数据打印
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print("\n" + "="*80)
                print(f"📊 K线实时跟踪 - {current_time} (定时更新)")
                print("="*80)
                print(f"当前价格: {latest_kline['close_price']:.2f}")
                print(f"开盘价: {latest_kline['open_price']:.2f}")
                print(f"最高价: {latest_kline['high_price']:.2f}")
                print(f"最低价: {latest_kline['low_price']:.2f}")
                print(f"成交量: {latest_kline['volume']:.2f}")
                print("="*80)
                
                # 计算最近N个周期的涨跌（以当前时间为终点）
                price_changes = calculate_price_change(data_df, latest_kline=latest_kline, interval=interval, periods=periods)
                
                if price_changes:
                    print(f"\n📈 最近{periods}个周期的涨跌情况:")
                    print("-"*80)
                    for change_info in price_changes:
                        period_num = change_info['period']
                        direction_emoji = "🟢" if change_info['direction'] == '涨' else "🔴"
                        print(f"周期 #{period_num} ({change_info['time']}):")
                        print(f"  开盘价: {change_info['open_price']:.2f}")
                        print(f"  收盘价: {change_info['close_price']:.2f}")
                        print(f"  涨跌: {direction_emoji} {change_info['direction']} {abs(change_info['change']):.2f} ({change_info['change_pct']:+.2f}%)")
                        print()
                else:
                    print(f"\n⚠️  数据不足，无法计算最近{periods}个周期的涨跌")
                    print(f"   当前数据量: {len(data_df) if data_df is not None else 0} 条")
                
                print("="*80 + "\n")
    
    # 创建定时打印任务
    print_task = asyncio.create_task(periodic_print())
    
    # 运行跟踪器
    try:
        # 保持运行直到中断
        while tracker.is_running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在停止...")
    finally:
        # 取消定时任务
        print_task.cancel()
        try:
            await print_task
        except asyncio.CancelledError:
            pass
        
        await tracker.stop()
        print("✅ 跟踪已停止")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='实时跟踪K线，并显示最近3个周期的涨跌和涨跌幅度')
    parser.add_argument('--symbol', type=str, default='ETHUSDT', help='交易对符号，例如 BTCUSDT, ETHUSDT')
    parser.add_argument('--interval', type=str, default='10m', help='时间间隔，例如 1m, 5m, 30m, 1h')
    parser.add_argument('--periods', type=int, default=4, help='要显示的最近周期数（默认3）')
    parser.add_argument('--ssl-verify', action='store_true', help='是否验证SSL证书（默认不验证）')
    
    args = parser.parse_args()
    
    # 运行异步跟踪
    asyncio.run(track_klines(
        symbol=args.symbol,
        interval=args.interval,
        periods=args.periods,
        ssl_verify=args.ssl_verify
    ))


if __name__ == "__main__":
    main()

