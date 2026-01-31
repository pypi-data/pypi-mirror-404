"""
LimitOrderHelper - 高性能数据批量写入助手

使用独立事件循环的 asyncio 实现，消除 GIL 影响，提升性能。

特性：
- 外部同步接口，内部 asyncio 实现
- 独立线程运行事件循环，无 GIL 竞争
- 适配所有交易所 SDK（同步/异步）
- 线程安全的跨线程调用
"""

import asyncio
import datetime
import threading
from typing import Callable, Optional

import pandas as pd
from kaq_quant_common.resources.kaq_ddb_stream_write_resources import (
    KaqQuantDdbStreamMTWWriteRepository,
    KaqQuantDdbStreamWriteRepository,
)
from kaq_quant_common.utils import logger_utils


class LimitOrderHelper:
    """
    使用独立事件循环的高性能数据批量写入助手

    架构说明：
    1. 外部通过同步方法 push_data() 推送数据（适配任意 SDK）
    2. 内部使用独立线程运行 asyncio 事件循环
    3. 数据通过 asyncio.Queue 缓冲，定时批量写入数据库
    4. 消除 GIL 锁竞争，提升高频场景性能
    """

    def __init__(
        self,
        ddb: KaqQuantDdbStreamWriteRepository | KaqQuantDdbStreamMTWWriteRepository,
        ddb_table_name: str,
        _flush_interval_ms: int = 100,
        max_queue_size: int = 10000,
    ):
        """
        初始化 LimitOrderHelper

        Args:
            ddb: DDB 数据库连接（支持普通或 MTW 版本）
            ddb_table_name: 数据库表名
            _flush_interval_ms: 刷新间隔（毫秒），默认 100ms
            max_queue_size: 队列最大容量，默认 10000
        """
        # DDB 相关
        self._ddb = ddb
        self._isMtwDdb = isinstance(self._ddb, KaqQuantDdbStreamMTWWriteRepository)
        self._ddb_table_name = ddb_table_name

        # 配置参数
        self._flush_interval_ms = _flush_interval_ms
        self._max_queue_size = max_queue_size

        # 异步组件（将在后台线程中创建）
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._data_queue: Optional[asyncio.Queue] = None
        self._flusher_task: Optional[asyncio.Task] = None

        # 线程控制
        self._event_loop_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._started = threading.Event()

        # 日志和回调
        self._logger = logger_utils.get_logger(self)
        self._build_data: Optional[Callable] = None

    def set_build_data(self, build_data: Callable):
        """
        设置数据构建函数

        Args:
            build_data: 回调函数，签名为 (symbol, data, arg) -> list | DataFrame
        """
        self._build_data = build_data

    def push_data(self, symbol: str, data: dict, arg: dict = None):
        """
        同步接口：推送数据到队列

        该方法是线程安全的，可从任何线程调用。
        内部使用 call_soon_threadsafe 将数据投递到异步队列。

        Args:
            symbol: 交易对符号
            data: 数据字典
            arg: 可选参数
        """
        if not self._started.is_set():
            self._logger.warning("Helper 未启动，数据被丢弃")
            return

        # 使用 call_soon_threadsafe 将数据投递到异步队列
        self._loop.call_soon_threadsafe(self._async_push_data, symbol, data, arg)

    def _async_push_data(self, symbol: str, data: dict, arg: dict):
        """
        内部方法：异步推送数据（在事件循环线程中执行）

        Args:
            symbol: 交易对符号
            data: 数据字典
            arg: 可选参数
        """
        try:
            # 非阻塞推送
            self._data_queue.put_nowait((symbol, data, arg))
        except asyncio.QueueFull:
            self._logger.warning(f"队列已满 ({self._max_queue_size})，丢弃 {symbol} 数据")

    def start(self):
        """启动后台线程和事件循环"""
        if self._event_loop_thread is not None:
            self._logger.warning("Helper 已经启动")
            return

        self._stop_event.clear()

        # 启动后台线程
        self._event_loop_thread = threading.Thread(target=self._run_event_loop, daemon=True, name="LimitOrderHelperAsyncThread")
        self._event_loop_thread.start()

        # 等待事件循环就绪
        self._started.wait(timeout=5.0)

        if not self._started.is_set():
            raise RuntimeError("事件循环启动超时")

        self._logger.info("LimitOrderHelper 启动成功（asyncio 模式）")

    def stop(self):
        """优雅停止"""
        if not self._started.is_set():
            return

        self._logger.info("正在停止 LimitOrderHelper...")

        # 设置停止标志
        self._stop_event.set()

        # 取消刷新任务
        if self._loop and self._flusher_task and not self._flusher_task.done():
            self._loop.call_soon_threadsafe(self._flusher_task.cancel)
            # 等待任务取消完成
            import time

            time.sleep(0.1)

        # 如果事件循环正在运行，停止它
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        # 等待线程结束
        if self._event_loop_thread:
            self._event_loop_thread.join(timeout=10.0)
            if self._event_loop_thread.is_alive():
                self._logger.error("事件循环线程未能正常退出")

        self._logger.info("LimitOrderHelper 已停止")

    def _run_event_loop(self):
        """
        在独立线程中运行事件循环
        """
        try:
            # 创建新的事件循环
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            # 创建异步队列
            self._data_queue = asyncio.Queue(maxsize=self._max_queue_size)

            # 创建后台刷新任务
            self._flusher_task = self._loop.create_task(self._flush_loop())

            # 标记已启动
            self._started.set()

            # 运行事件循环
            self._loop.run_forever()

        except Exception as e:
            self._logger.error(f"事件循环异常: {e}", exc_info=True)
        finally:
            # 清理
            try:
                # 取消所有任务
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()

                # 等待任务完成
                if pending:
                    self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

                # 关闭事件循环
                self._loop.close()
            except Exception as e:
                self._logger.error(f"清理事件循环时出错: {e}")

    async def _flush_loop(self):
        """
        异步刷新循环（在事件循环线程中执行）

        定时从队列批量获取数据并写入数据库。
        """
        cum_count = 0
        cum_total_use_time = 0

        try:
            while not self._stop_event.is_set():
                # 批量收集数据
                batch = {}
                deadline = asyncio.get_event_loop().time() + self._flush_interval_ms / 1000.0

                # 在时间窗口内尽可能多地收集数据
                while asyncio.get_event_loop().time() < deadline:
                    try:
                        remaining_time = deadline - asyncio.get_event_loop().time()
                        if remaining_time <= 0:
                            break

                        # 从队列获取数据（带超时）
                        symbol, data, arg = await asyncio.wait_for(self._data_queue.get(), timeout=remaining_time)

                        # 只保留每个 symbol 的最新数据（去重）
                        batch[symbol] = (data, arg)

                    except asyncio.TimeoutError:
                        break

                # 如果有数据，批量写入
                if batch:
                    start_time = datetime.datetime.now()

                    try:
                        await self._write_to_db(batch)
                    except Exception as e:
                        self._logger.error(f"批量写入失败: {e}", exc_info=True)

                    # 统计
                    end_time = datetime.datetime.now()
                    total_use_time = (end_time - start_time).total_seconds() * 1000

                    cum_count += len(batch)
                    cum_total_use_time += total_use_time

                    # if total_use_time > 500:
                    #     self._logger.debug(
                    #         f"批量写入 {len(batch)} 条数据耗时 {total_use_time:.2f}ms "
                    #         f"(avg {cum_total_use_time / cum_count:.2f}ms)"
                    #     )
                else:
                    # 没有数据时短暂休眠
                    await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            self._logger.info("刷新循环被取消")
        except Exception as e:
            self._logger.error(f"刷新循环异常: {e}", exc_info=True)

    async def _write_to_db(self, batch: dict):
        """
        写入数据库（异步）

        Args:
            batch: 批量数据字典，格式为 {symbol: (data, arg)}
        """
        # 如果已经停止，直接返回
        if self._stop_event.is_set():
            self._logger.warning("Helper 正在停止，跳过本次写入")
            return
        # 转换数据
        df: Optional[pd.DataFrame] = None
        list_data: list = []

        for symbol, (data, arg) in batch.items():
            sub_data = self._build_data(symbol, data, arg)

            if sub_data is None or len(sub_data) == 0:
                continue

            if not self._isMtwDdb:
                # DataFrame 方式
                if isinstance(sub_data, pd.DataFrame):
                    df = sub_data if df is None else pd.concat([df, sub_data], ignore_index=True)
                # List 方式
                else:
                    if isinstance(sub_data[0], list):
                        list_data.extend(sub_data)
                    else:
                        list_data.append(sub_data)
            else:
                # MTW 直接写入（使用 to_thread 包装同步调用）
                try:
                    await asyncio.to_thread(self._ddb.save2stream_list, sub_data)
                except Exception as e:
                    self._logger.error(f"MTW 写入失败: {e}")

        # 批量写入（使用 to_thread 包装同步 DDB 调用）
        if not self._isMtwDdb:
            if df is not None and not df.empty:
                try:
                    await asyncio.to_thread(self._ddb.save2stream_batch, self._ddb_table_name, df=df)
                except Exception as e:
                    self._logger.error(f"批量写入 DataFrame 失败: {e}")

            if list_data:
                try:
                    await asyncio.to_thread(self._ddb.save2stream_batch_list, self._ddb_table_name, data=list_data)
                except Exception as e:
                    self._logger.error(f"批量写入 List 失败: {e}")
