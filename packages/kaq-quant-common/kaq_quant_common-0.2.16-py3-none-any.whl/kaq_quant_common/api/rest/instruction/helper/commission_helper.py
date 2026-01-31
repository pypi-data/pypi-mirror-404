import json
import pandas as pd
from typing import Optional

from kaq_quant_common.utils import logger_utils


class CommissionHelper:
    """手续费助手，用于从Redis加载和获取交易对的手续费率"""

    def __init__(self, ins_server):
        # 必须放在这里 延迟引入，否则会有循环引用问题
        from kaq_quant_common.api.rest.instruction.instruction_server_base import (
            InstructionServerBase,
        )

        self._server: InstructionServerBase = ins_server
        self._logger = logger_utils.get_logger(self)

        # 手续费数据缓存
        self._commission_data: Optional[pd.DataFrame] = None
        # 是否已加载
        self._loaded = False

    def _load_commission_rates(self):
        """从Redis加载手续费率数据"""
        if self._loaded:
            return

        redis = self._server._redis
        if redis is None:
            self._logger.warning("Redis未配置，无法加载手续费率")
            return

        exchange = self._server._exchange
        # 组装Redis key，格式: kaq_{exchange}_futures_commission_rate
        redis_key = f"kaq_{exchange}_futures_commission_rate"

        try:
            self._logger.info(f"Loading commission rates from Redis key: {redis_key}")
            # 从Redis读取list数据
            data_list = redis.lrange(redis_key)
            
            if data_list is not None and not data_list.empty:
                self._commission_data = data_list
                self._loaded = True
                self._logger.info(
                    f"Successfully loaded {len(self._commission_data)} commission rates"
                )
            else:
                self._logger.warning(f"No commission rate data found in Redis key: {redis_key}")
        except Exception as e:
            self._logger.error(f"Failed to load commission rates from Redis: {e}")

    def get_taker_commission_rate(self, symbol: str, default_rate: float = 0.0005) -> float:
        """
        获取指定交易对的taker手续费率

        Args:
            symbol: 交易对，如 BTCUSDT
            default_rate: 默认手续费率，如果获取失败则使用该值

        Returns:
            float: taker手续费率
        """
        # 如果还没加载，先加载
        if not self._loaded:
            self._load_commission_rates()

        # 如果还是没有数据，返回默认值
        if self._commission_data is None or self._commission_data.empty:
            self._logger.warning(
                f"Commission data not available, using default rate: {default_rate}"
            )
            return default_rate

        try:
            # 从DataFrame中查找对应的symbol
            matched = self._commission_data[self._commission_data["symbol"] == symbol]
            
            if not matched.empty:
                rate = float(matched.iloc[0]["takerCommissionRate"])
                self._logger.debug(f"Found taker commission rate for {symbol}: {rate}")
                return rate
            else:
                self._logger.warning(
                    f"Symbol {symbol} not found in commission data, using default rate: {default_rate}"
                )
                return default_rate
        except Exception as e:
            self._logger.error(
                f"Error getting commission rate for {symbol}: {e}, using default rate: {default_rate}"
            )
            return default_rate

    def get_maker_commission_rate(self, symbol: str, default_rate: float = 0.0002) -> float:
        """
        获取指定交易对的maker手续费率

        Args:
            symbol: 交易对，如 BTCUSDT
            default_rate: 默认手续费率，如果获取失败则使用该值

        Returns:
            float: maker手续费率
        """
        # 如果还没加载，先加载
        if not self._loaded:
            self._load_commission_rates()

        # 如果还是没有数据，返回默认值
        if self._commission_data is None or self._commission_data.empty:
            self._logger.warning(
                f"Commission data not available, using default rate: {default_rate}"
            )
            return default_rate

        try:
            # 从DataFrame中查找对应的symbol
            matched = self._commission_data[self._commission_data["symbol"] == symbol]
            
            if not matched.empty:
                rate = float(matched.iloc[0]["makerCommissionRate"])
                self._logger.debug(f"Found maker commission rate for {symbol}: {rate}")
                return rate
            else:
                self._logger.warning(
                    f"Symbol {symbol} not found in commission data, using default rate: {default_rate}"
                )
                return default_rate
        except Exception as e:
            self._logger.error(
                f"Error getting commission rate for {symbol}: {e}, using default rate: {default_rate}"
            )
            return default_rate

    def reload(self):
        """重新加载手续费率数据"""
        self._loaded = False
        self._commission_data = None
        self._load_commission_rates()
