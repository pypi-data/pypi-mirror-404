"""
Web3 / 链上 K 线数据获取（dquery.sintral.io u-kline API）

通过 dquery.sintral.io 的 u-kline 接口获取指定合约地址的 K 线数据，
支持 BSC 等链、按 USD 计价、多周期。
"""

import os
import logging
import csv
import json
import time
import requests
from datetime import datetime
from typing import Optional, Union, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 默认 API 基础 URL（与 curl 示例一致）
DEFAULT_BASE_URL = "https://dquery.sintral.io/u-kline/v1/k-line/candles"


def _convert_to_timestamp_ms(time_input: Union[datetime, str, int, None]) -> Optional[int]:
    """
    将各种时间格式转换为毫秒时间戳

    Args:
        time_input: 时间输入，可以是：
                   - datetime 对象
                   - 字符串格式的时间，例如 '2023-01-01 00:00:00' 或 '2023-01-01'
                   - 整数时间戳（秒或毫秒，自动判断）
                   - None

    Returns:
        毫秒时间戳，如果输入为 None 则返回 None
    """
    if time_input is None:
        return None

    if isinstance(time_input, datetime):
        return int(time_input.timestamp() * 1000)

    if isinstance(time_input, str):
        try:
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d']:
                try:
                    dt = datetime.strptime(time_input, fmt)
                    return int(dt.timestamp() * 1000)
                except ValueError:
                    continue
            raise ValueError(f"无法解析时间字符串: {time_input}")
        except Exception as e:
            logging.error(f"时间字符串解析失败: {e}")
            raise

    if isinstance(time_input, int):
        if time_input > 1e10:
            return time_input
        return time_input * 1000

    raise TypeError(f"不支持的时间类型: {type(time_input)}")


def _get_interval_duration_ms(interval: str) -> int:
    """
    将 u-kline 的 interval 字符串（如 1min, 1h）转为单根 K 线对应的毫秒数。
    """
    interval = (interval or "").strip().lower()
    # 支持 1min, 5min, 15min, 1h, 4h, 1d 等
    mapping = {
        "1min": 60 * 1000,
        "3min": 3 * 60 * 1000,
        "5min": 5 * 60 * 1000,
        "15min": 15 * 60 * 1000,
        "30min": 30 * 60 * 1000,
        "1h": 60 * 60 * 1000,
        "2h": 2 * 60 * 60 * 1000,
        "4h": 4 * 60 * 60 * 1000,
        "6h": 6 * 60 * 60 * 1000,
        "12h": 12 * 60 * 60 * 1000,
        "1d": 24 * 60 * 60 * 1000,
        "3d": 3 * 24 * 60 * 60 * 1000,
        "1w": 7 * 24 * 60 * 60 * 1000,
    }
    if interval in mapping:
        return mapping[interval]
    # 兼容 1m 等形式
    if interval == "1m":
        return 60 * 1000
    if interval.endswith("m") and interval[:-1].isdigit():
        return int(interval[:-1]) * 60 * 1000
    if interval.endswith("h") and interval[:-1].isdigit():
        return int(interval[:-1]) * 60 * 60 * 1000
    if interval.endswith("d") and interval[:-1].isdigit():
        return int(interval[:-1]) * 24 * 60 * 60 * 1000
    return 60 * 1000  # 默认 1 分钟


def _address_to_slug(address: str, max_len: int = 12) -> str:
    """将合约地址转为短标识，用于文件名。"""
    addr = (address or "").strip().lower()
    if not addr:
        return "unknown"
    if addr.startswith("0x"):
        return addr[2:2 + max_len] if len(addr) > 2 else addr[2:]
    return addr[:max_len]


def _timestamp_ms_to_str(ts_ms: int) -> str:
    """将毫秒时间戳转为可读字符串；若 ts_ms 像秒（<1e11），则按秒解释。"""
    if ts_ms < 1e11:
        ts_ms = int(ts_ms) * 1000
    return datetime.fromtimestamp(int(ts_ms) / 1000).strftime("%Y-%m-%d %H:%M:%S")


def _parse_candle_row(row: Any, index: int, interval_ms: Optional[int] = None) -> Optional[dict]:
    """
    将 u-kline API 返回的一行 K 线解析为统一结构。

    u-kline 数组布局与 Binance 不同，为: [?, open, high, low, close, open_time_ms, ?, ...]
    即 index 5 为开盘时间（毫秒），close_time 由 open_time + interval_ms - 1 得到。
    也兼容返回为字典的情况。
    """
    if row is None:
        return None
    if isinstance(row, dict):
        open_time = row.get("open_time") or row.get("openTime") or row.get(0)
        open_p = row.get("open") or row.get("open_price") or row.get(1)
        high = row.get("high") or row.get(2)
        low = row.get("low") or row.get(3)
        close = row.get("close") or row.get("close_price") or row.get(4)
        volume = row.get("volume") or row.get(5)
        close_time = row.get("close_time") or row.get("closeTime") or row.get(6)
        quote_volume = row.get("quote_volume", row.get("quoteVolume", row.get(7, 0)))
        trades = row.get("trades", row.get(8, 0))
        taker_buy_base = row.get("taker_buy_base_volume", row.get(9, 0))
        taker_buy_quote = row.get("taker_buy_quote_volume", row.get(10, 0))
        ignore = row.get("ignore", row.get(11, 0))
    elif isinstance(row, (list, tuple)):
        if len(row) < 6:
            return None
        # u-kline 布局: [?, open, high, low, close, open_time_ms, ...]
        open_p = row[1]
        high = row[2]
        low = row[3]
        close = row[4]
        open_time_raw = row[5]
        if interval_ms is not None:
            # u-kline 布局: index 5 = open_time(ms)，close_time = open_time + interval - 1
            open_time_ms = int(float(open_time_raw))
            if open_time_ms < 1e11:
                open_time_ms = open_time_ms * 1000
            close_time_ms = open_time_ms + interval_ms - 1
            open_time = open_time_ms
            close_time = close_time_ms
            volume = 0.0  # u-kline 数组未提供 volume 字段
            quote_volume = 0.0
            trades = 0
            taker_buy_base = 0.0
            taker_buy_quote = 0.0
            ignore = 0
        else:
            open_time = row[0]
            close_time = row[6] if len(row) > 6 else 0
            volume = row[5]
            quote_volume = row[7] if len(row) > 7 else 0
            trades = row[8] if len(row) > 8 else 0
            taker_buy_base = row[9] if len(row) > 9 else 0
            taker_buy_quote = row[10] if len(row) > 10 else 0
            ignore = row[11] if len(row) > 11 else 0
    else:
        return None

    try:
        open_time = int(open_time)
        close_time = int(close_time)
        if open_time < 1e11:
            open_time = open_time * 1000
        if close_time < 1e11:
            close_time = close_time * 1000
        return {
            "open_time": open_time,
            "open_time_str": _timestamp_ms_to_str(open_time),
            "open_price": float(open_p),
            "high_price": float(high),
            "low_price": float(low),
            "close_price": float(close),
            "volume": float(volume),
            "close_time": close_time,
            "close_time_str": _timestamp_ms_to_str(close_time),
            "quote_volume": float(quote_volume),
            "trades": int(trades),
            "taker_buy_base_volume": float(taker_buy_base),
            "taker_buy_quote_volume": float(taker_buy_quote),
            "ignore": ignore,
        }
    except (TypeError, ValueError) as e:
        logging.debug(f"跳过第 {index} 行解析: {e}")
        return None


def get_and_save_web3_klines(
    address: str,
    platform: str = "BSC",
    unit: str = "usd",
    interval: str = "1min",
    start_time: Optional[Union[datetime, str, int]] = None,
    end_time: Optional[Union[datetime, str, int]] = None,
    n: int = 1500,
    output_dir: str = "data",
    save_csv: bool = False,
    save_json: bool = True,
    base_url: Optional[str] = None,
    timeout: tuple = (30, 60),
) -> Optional[List[dict]]:
    """
    请求 dquery.sintral.io u-kline 接口，获取指定合约的 K 线并保存。

    参数与 curl 示例对应：
        platform: 链，如 BSC
        unit: 计价单位，如 usd
        interval: 周期，如 1min
        address: 合约地址
        start_time / end_time: 时间范围；若两者都缺失，则 end_time 默认为当前时间，并取 n 个点

    Args:
        address: 合约地址，例如 '0xe6df05ce8c8301223373cf5b969afcb1498c5528'
        platform: 链标识，默认 'BSC'
        unit: 计价单位，默认 'usd'
        interval: K 线周期，默认 '1min'
        start_time: 开始时间；与 end_time 同时缺失时可不填
        end_time: 结束时间；与 start_time 同时缺失时默认为当前时间
        n: 当 start_time 与 end_time 都未提供时，按当前时间为 end_time，向前取 n 根 K 线（默认 1500）
        output_dir: 输出目录，默认 'data'
        save_csv: 是否保存 CSV，默认 False
        save_json: 是否保存 JSON，默认 True
        base_url: API 地址，默认使用 DEFAULT_BASE_URL
        timeout: (connect_timeout, read_timeout)，默认 (30, 60)

    Returns:
        解析后的 K 线列表（每项为 dict），失败返回 None
    """
    base_url = base_url or os.getenv("U_KLINE_BASE_URL", DEFAULT_BASE_URL)
    start_time_ms = _convert_to_timestamp_ms(start_time) if start_time is not None else None
    end_time_ms = _convert_to_timestamp_ms(end_time) if end_time is not None else None

    if start_time_ms is None and end_time_ms is None:
        end_time_ms = int(datetime.now().timestamp() * 1000)
        interval_ms = _get_interval_duration_ms(interval)
        start_time_ms = end_time_ms - n * interval_ms
        logging.info(f"未指定时间范围：使用 end_time=当前时间，取 n={n} 根 K 线，start_time 由 interval 反推")
    elif start_time_ms is None or end_time_ms is None:
        logging.error("Web3 K 线接口需同时提供 start_time 和 end_time，或两者都不提供以使用默认（当前时间 + n 点）")
        return None

    if start_time_ms >= end_time_ms:
        logging.error("start_time 必须小于 end_time")
        return None

    params = {
        "platform": platform,
        "unit": unit,
        "interval": interval,
        "address": address.strip(),
        "from": start_time_ms,
        "to": end_time_ms,
    }

    time_info = (
        f"from {datetime.fromtimestamp(start_time_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')} "
        f"to {datetime.fromtimestamp(end_time_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')}"
    )
    logging.info(f"请求 Web3 K 线: {platform} {address[:10]}... 间隔={interval}, {time_info}")

    try:
        response = requests.get(base_url, params=params, timeout=timeout)
        response.raise_for_status()
        raw = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"请求 u-kline 失败: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"解析响应 JSON 失败: {e}")
        return None

    # 兼容：直接数组 / 包装在 data 或 candles 等字段中
    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict):
        rows = raw.get("data", raw.get("candles", raw.get("result", [])))
        if not isinstance(rows, list):
            rows = [raw] if raw else []
    else:
        rows = []

    interval_ms = _get_interval_duration_ms(interval)
    formatted = []
    for i, row in enumerate(rows):
        parsed = _parse_candle_row(row, i, interval_ms=interval_ms)
        if parsed:
            formatted.append(parsed)

    if not formatted:
        logging.warning("未解析到任何 K 线数据")
        return None

    logging.info(f"成功获取 {len(formatted)} 条 Web3 K 线")

    # 输出目录与文件名
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"创建目录: {output_dir}")

    slug = _address_to_slug(address)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_str = datetime.fromtimestamp(start_time_ms / 1000).strftime("%Y%m%d_%H%M%S")
    end_str = datetime.fromtimestamp(end_time_ms / 1000).strftime("%Y%m%d_%H%M%S")
    base_filename = f"web3_{platform}_{slug}_{interval}_{len(formatted)}_{start_str}_{end_str}_{timestamp}"

    if save_csv:
        csv_path = os.path.join(output_dir, f"{base_filename}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "开盘时间", "开盘价", "最高价", "最低价", "收盘价",
                "成交量", "收盘时间", "成交额", "成交笔数",
                "主动买入成交量", "主动买入成交额", "忽略",
            ])
            for c in formatted:
                writer.writerow([
                    c["open_time_str"], c["open_price"], c["high_price"], c["low_price"], c["close_price"],
                    c["volume"], c["close_time_str"], c["quote_volume"], c["trades"],
                    c["taker_buy_base_volume"], c["taker_buy_quote_volume"], c.get("ignore", 0),
                ])
        logging.info(f"已保存 CSV: {csv_path}")

    if save_json:
        json_path = os.path.join(output_dir, f"{base_filename}.json")
        metadata = {
            "source": "u-kline",
            "base_url": base_url,
            "address": address,
            "platform": platform,
            "unit": unit,
            "interval": interval,
            "start_time": start_time_ms,
            "start_time_str": datetime.fromtimestamp(start_time_ms / 1000).strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time_ms,
            "end_time_str": datetime.fromtimestamp(end_time_ms / 1000).strftime("%Y-%m-%d %H:%M:%S"),
            "data_count": len(formatted),
            "timestamp": timestamp,
            "data": formatted,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logging.info(f"已保存 JSON: {json_path}")

    return formatted


if __name__ == "__main__":
    # 示例1：不传 start_time/end_time，默认 end_time=当前时间，取 n=1500 根 K 线
    get_and_save_web3_klines(
        address="0xe6df05ce8c8301223373cf5b969afcb1498c5528",
        platform="BSC",
        unit="usd",
        interval="1min",
        n=1500,
        output_dir="/Users/user/Desktop/repo/crypto_trading/cyqnt_trd/tmp/data/web3_klines",
        save_csv=False,
        save_json=True,
    )

    # 示例2：指定时间范围（与 curl 等价）
    # get_and_save_web3_klines(
    #     address="0xe6df05ce8c8301223373cf5b969afcb1498c5528",
    #     platform="BSC",
    #     unit="usd",
    #     interval="1min",
    #     start_time=1765764600000,
    #     end_time=1765768139999,
    #     output_dir="/Users/user/Desktop/repo/crypto_trading/cyqnt_trd/tmp/data/web3_klines",
    #     save_csv=False,
    #     save_json=True,
    # )
