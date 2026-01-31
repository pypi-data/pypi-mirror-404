import json
import time
from typing import Optional

from kaq_quant_common.api.rest.instruction.models.order import (
    OrderInfo,
    OrderSide,
    OrderStatus,
    PositionStatus,
)
from kaq_quant_common.api.rest.instruction.models.position import PositionSide
from kaq_quant_common.utils import logger_utils, uuid_utils


class MockOrderHelper:
    """模拟订单助手，用于模拟下单流程，不调用真实交易所API"""

    def __init__(self, ins_server):
        # 必须放在这里 延迟引入，否则会有循环引用问题
        from kaq_quant_common.api.rest.instruction.instruction_server_base import (
            InstructionServerBase,
        )

        self._server: InstructionServerBase = ins_server
        self._logger = logger_utils.get_logger(self)

        self._mysql_table_name_order = "kaq_futures_instruction_order"
        self._mysql_table_name_position = "kaq_futures_instruction_position"
        # 当前持仓
        self._redis_key_position = "kaq_futures_instruction_position"
        # 持仓历史
        self._redis_key_position_history = "kaq_futures_instruction_position_history"

    def _write_position_open_to_redis(
        self,
        position_id: str,
        exchange: str,
        symbol: str,
        position_side,
        lever: int,
        coin_quantity: float,
        usdt_quantity: float,
        open_ins_id: str,
        open_price: float,
        open_fee: float,
        open_fee_rate: float,
        open_time: int,
        is_spot: bool,
    ):
        redis = self._server._redis
        if redis is None:
            return
        data = {
            "id": position_id,
            "exchange": exchange,
            "symbol": symbol,
            "position_side": position_side.value,
            "lever": lever,
            "coin_quantity": coin_quantity,
            "usdt_quantity": usdt_quantity,
            "open_ins_id": open_ins_id,
            "open_price": open_price,
            "open_fee": open_fee,
            "open_fee_rate": open_fee_rate,
            "open_time": open_time,
            "close_ins_id": None,
            "close_price": 0,
            "close_time": 0,
            "status": PositionStatus.OPEN.value,
            "is_spot": is_spot,
            # 标识模拟
            "is_mock": True,
        }
        redis.client.hset(self._redis_key_position, position_id, json.dumps(data))

    def _write_position_close_to_redis(
        self,
        position_id: str,
        exchange: str,
        symbol: str,
        position_side,
        lever: int,
        coin_quantity: float,
        usdt_quantity: float,
        open_ins_id: str,
        open_price: float,
        open_fee: float,
        open_fee_rate: float,
        open_time: int,
        close_ins_id: str,
        close_price: float,
        close_fee: float,
        close_fee_rate: float,
        close_time: int,
        is_spot: bool,
    ):
        redis = self._server._redis
        if redis is None:
            return

        # 先从 redis 读取现有的 position 数据，获取 funding_rate_records 字段
        funding_rate_records = None
        try:
            existing_position_json = redis.client.hget(self._redis_key_position, position_id)
            if existing_position_json:
                existing_position = json.loads(existing_position_json)
                if existing_position and "funding_rate_records" in existing_position:
                    funding_rate_records = existing_position.get("funding_rate_records")
        except Exception as e:
            # 读取失败不影响后续流程，记录日志
            self._logger.warning(f"Failed to get funding_rate_records for position {position_id}: {e}")

        data = {
            "id": position_id,
            "exchange": exchange,
            "symbol": symbol,
            "position_side": position_side.value,
            "lever": lever,
            "coin_quantity": coin_quantity,
            "usdt_quantity": usdt_quantity,
            "open_ins_id": open_ins_id,
            "open_price": open_price,
            "open_fee": open_fee,
            "open_fee_rate": open_fee_rate,
            "open_time": open_time,
            "close_ins_id": close_ins_id,
            "close_price": close_price,
            "close_fee": close_fee,
            "close_fee_rate": close_fee_rate,
            "close_time": close_time,
            "status": PositionStatus.CLOSE.value,
            "is_spot": is_spot,
            # 标识模拟
            "is_mock": True,
        }

        # 如果存在 funding_rate_records，添加到 data 中
        if funding_rate_records is not None:
            data["funding_rate_records"] = funding_rate_records

        redis.client.hdel(self._redis_key_position, position_id)
        redis.client.rpush(self._redis_key_position_history, json.dumps(data))

    def process_order(
        self,
        order: OrderInfo,
        mock_fill_price: Optional[float] = None,
        mock_fee_rate: float = 0.0005,
    ):
        """
        处理模拟订单

        Args:
            order: 订单信息
            mock_fill_price: 模拟成交价格，如果为None则使用订单的target_price
            mock_fee_rate: 模拟手续费率，默认0.05%
        """
        # 获取交易所
        exchange = self._server._exchange

        # 记录开始时间
        start_time = time.time()

        # 执行模拟订单处理
        self._do_process_mock_order(exchange, order, mock_fill_price, mock_fee_rate, start_time)

    def _do_process_mock_order(
        self,
        exchange: str,
        order: OrderInfo,
        mock_fill_price: Optional[float],
        mock_fee_rate: float,
        start_time: float,
    ):
        # 获取mysql
        mysql = self._server._mysql

        ins_id = order.instruction_id
        order_id = order.order_id
        symbol = order.symbol
        side = order.side
        position_side = order.position_side
        lever = order.level
        # TODO
        is_spot = False

        is_open = True
        side_str = "开仓"
        if position_side == PositionSide.LONG:
            # 多单是正向理解的
            if side == OrderSide.SELL:
                side_str = "平仓"
                is_open = False
            else:
                side_str = "开仓"
                is_open = True
        else:
            # 空单是反向理解的
            if side == OrderSide.SELL:
                side_str = "开仓"
                is_open = True
            else:
                side_str = "平仓"
                is_open = False

        self._logger.info(f"[MOCK] {ins_id}_{exchange}_{symbol} step 1. {"现货" if is_spot else "合约"}{side_str}模拟挂单 {order_id}")

        # 步骤1.挂单成功 插入到订单记录
        current_time = int(time.time() * 1000)

        if mysql is not None:
            status = OrderStatus.CREATE
            sql = f"""
            INSERT INTO {self._mysql_table_name_order} (ins_id, exchange, symbol, side, position_side, lever, orig_price, orig_coin_quantity, order_id, status, create_time, last_update_time, is_spot, is_mock) 
            VALUES ( '{ins_id}', '{exchange}', '{symbol}', '{side.value}', '{order.position_side.value}', '{lever}', {order.current_price or order.target_price}, {order.quantity}, '{order_id}', '{status.value}', {current_time}, {current_time}, '{1 if is_spot else 0}', 1 );
            """
            execute_ret = mysql.execute_sql(sql, True)

        # 步骤2.模拟成交 - 直接使用模拟价格
        # 如果没有指定模拟成交价，使用订单的当前价格
        avg_price = mock_fill_price if mock_fill_price is not None else order.current_price or order.target_price
        # 成交数量就是订单数量
        executed_qty = order.quantity
        # 计算出usdt数量
        executed_usdt = avg_price * executed_qty
        # 计算手续费
        fee = executed_usdt * mock_fee_rate
        # 费率
        fee_rate = mock_fee_rate

        # 模拟处理时间（可以立即完成）
        end_time = time.time()
        cost_time = end_time - start_time

        self._logger.info(f"[MOCK] {ins_id}_{exchange}_{symbol} step 2. {side_str}模拟订单 {order_id} 成交 耗时 {int(cost_time * 1000)}ms")

        # 步骤3.把最终持仓写进去
        current_time = int(time.time() * 1000)

        if mysql is None:
            self._logger.warning(f"[MOCK] {ins_id}_{exchange}_{symbol} 仅操作，没有入库，请设置 mysql!!")
            return

        status = OrderStatus.FINISH
        # 更新写入最终信息
        sql = f"""
        UPDATE {self._mysql_table_name_order} 
        SET price = {avg_price}, coin_quantity = {executed_qty}, usdt_quantity = {executed_usdt}, fee = {fee}, fee_rate = {fee_rate}, status = '{status.value}', last_update_time = {current_time} 
        WHERE ins_id = '{ins_id}' AND exchange = '{exchange}' AND symbol = '{symbol}';
        """
        execute_ret = mysql.execute_sql(sql, True)

        self._logger.info(
            f"[MOCK] {ins_id}_{exchange}_{symbol} step 2. 模拟订单成交 {order_id}, {side_str}价格 {avg_price}, {side_str}数量 {executed_qty}, {side_str}usdt {executed_usdt} 杠杆 {lever}"
        )

        if is_open:
            # 同时插入持仓表
            position_id = uuid_utils.generate_uuid()
            sql = f"""
            INSERT INTO {self._mysql_table_name_position} (id, exchange, symbol, position_side, lever, coin_quantity, usdt_quantity, open_ins_id, open_price, open_fee, open_fee_rate, open_time, status, is_spot, is_mock) 
            VALUES ( '{position_id}', '{exchange}', '{symbol}', '{position_side.value}', '{lever}', '{executed_qty}', '{executed_usdt}', '{ins_id}', '{avg_price}', '{fee}', '{fee_rate}', {current_time}, '{PositionStatus.OPEN.value}', '{1 if is_spot else 0}', 1 );
            """
            execute_ret = mysql.execute_sql(sql, True)

            self._logger.info(f"[MOCK] {ins_id}_{exchange}_{symbol} step 3. 创建持仓记录 {position_id}")
            try:
                self._write_position_open_to_redis(
                    position_id=position_id,
                    exchange=exchange,
                    symbol=symbol,
                    position_side=position_side,
                    lever=lever,
                    coin_quantity=executed_qty,
                    usdt_quantity=executed_usdt,
                    open_ins_id=ins_id,
                    open_price=avg_price,
                    open_fee=fee,
                    open_fee_rate=fee_rate,
                    open_time=current_time,
                    is_spot=is_spot,
                )
            except:
                pass
        else:
            # 需要找到对应的持仓记录
            sql = f"""
            SELECT * FROM {self._mysql_table_name_position}
            WHERE exchange = '{exchange}' 
            AND symbol = '{symbol}' 
            AND position_side = '{position_side.value}' 
            AND status = '{PositionStatus.OPEN.value}' 
            AND is_spot = '{1 if is_spot else 0}'
            AND is_mock = 1 
            ORDER BY open_time ASC;
            """

            # 如果有指定仓位id，就用指定的
            if hasattr(order, "position_id") and order.position_id:
                sql = f"""
                SELECT * FROM {self._mysql_table_name_position}
                WHERE id = '{order.position_id}' AND status = '{PositionStatus.OPEN.value}' AND is_mock = 1
                """
                self._logger.info(f"[MOCK] {ins_id}_{exchange}_{symbol} get position by id {order.position_id}")

            execute_ret = mysql.execute_sql(sql)
            try:
                row = execute_ret.fetchone()
                position_id = row.id
                if position_id is not None:
                    # 更新持仓信息
                    sql = f"""
                    UPDATE {self._mysql_table_name_position} 
                    SET close_ins_id = '{ins_id}', close_price = {avg_price}, close_fee = '{fee}', close_fee_rate = '{fee_rate}', close_time = {current_time}, status = '{PositionStatus.CLOSE.value}'
                    WHERE id = '{position_id}';
                    """
                    execute_ret = mysql.execute_sql(sql, True)

                    self._logger.info(f"[MOCK] {ins_id}_{exchange}_{symbol} step 3. 更新持仓记录 {position_id}")
                    try:
                        self._write_position_close_to_redis(
                            position_id=position_id,
                            exchange=exchange,
                            symbol=symbol,
                            position_side=position_side,
                            lever=row.lever,
                            coin_quantity=float(row.coin_quantity),
                            usdt_quantity=float(row.usdt_quantity),
                            open_ins_id=row.open_ins_id,
                            open_price=float(row.open_price),
                            open_fee=float(row.open_fee),
                            open_fee_rate=float(row.open_fee_rate),
                            open_time=int(row.open_time),
                            close_ins_id=ins_id,
                            close_price=avg_price,
                            close_fee=fee,
                            close_fee_rate=fee_rate,
                            close_time=current_time,
                            is_spot=row.is_spot,
                        )
                    except:
                        pass
            except:
                pass

        return True
