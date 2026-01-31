import os
import queue
import threading
import time
import traceback
from typing import Optional, Union

import dolphindb as ddb
import numpy as np
import pandas as pd
from kaq_quant_common.utils import yml_utils
from kaq_quant_common.utils.logger_utils import get_logger
from typing_extensions import deprecated

mutex = threading.Lock()


# 方式一: 异步调用
class KaqQuantDdbStreamWriteRepository:
    """
    异步不等待写入
    """

    def __init__(self, host, port, user, passwd):
        self.logger = get_logger(self)
        """
        创建ddb连接 && 添加ddb流数据表支持
        """
        try:
            mutex.acquire()
            self.session = ddb.session(enableASYNC=True)
            self.session.connect(host, port, user, passwd, tryReconnectNums=100, reconnect=True, keepAliveTime=1000, readTimeout=10, writeTimeout=5)
            # 流表订阅用的
            # self.session.enableStreaming(threadCount=5)
            # self.pool = ddb.DBConnectionPool(host, port, userid=user, password=passwd, loadBalance=False, reConnect=True, tryReconnectNums=5, sqlStd=SqlStd.MySQL)

            # 需要注意的是 fetchSize 取值不能小于 8192 （记录条数）
            self.size = 8192
        except Exception as e:
            self.logger.error(f"KaqQuantDdbStreamWriteRepository.__init__ is occured error: {str(e)} - {str(traceback.format_exc())}")
        finally:
            mutex.release()

    def save_rows(self, ddb_table_name: str, rows: Optional[Union[np.ndarray, list]] = None):
        """
        调用此方法之前, 需要将dataframe中的字符串类型的值 ，添加引号
        """
        if rows is None:
            return
        # 获取维度
        if isinstance(rows[0], (list, np.ndarray, tuple)):
            # 多行数据
            try:
                formatted_values = []
                for row in rows:
                    # 这里的 row 是 np.array([1767708564161, "BTC", 92500.1])
                    row = [f"'{v}'" if isinstance(v, str) else str(v) for v in row]
                    formatted_values.append(f"({', '.join(row)})")
                script = f"insert into {ddb_table_name} values {', '.join(str(x) for x in formatted_values)}"

                self.session.run(script, clearMemory=True)
            except Exception as e:
                self.logger.error(
                    f"KaqQuantDdbStreamWriteRepository.save_rows is occured error: tableName is {ddb_table_name} - {str(e)} - {str(traceback.format_exc())}"
                )
        else:
            # 是一行数据，调用 insert
            formatted_values = [f"'{v}'" if isinstance(v, str) else str(v) for v in rows]
            script = f"insert into {ddb_table_name} values({', '.join(str(x) for x in formatted_values)})"
            try:
                self.session.run(script, clearMemory=True)
            except Exception as e:
                self.logger.error(
                    f"KaqQuantDdbStreamWriteRepository.save_rows is occured error: tableName is {ddb_table_name} - {str(e)} - {str(traceback.format_exc())}"
                )

    def save2stream(self, ddb_table_name: str, df: pd.DataFrame):
        """
        调用此方法之前, 需要将dataframe中的字符串类型的值 ，添加引号
        """
        # 遍历每列的数据类型
        for column, dtype in df.dtypes.items():
            if dtype == "object" or dtype == "str":
                df[column] = "'" + df[column] + "'"
        for index, row in df.iterrows():
            script = f"insert into {ddb_table_name} values({', '.join(str(x) for x in row.values)})"
            try:
                self.session.run(script, clearMemory=True)
            except Exception as e:
                self.logger.error(
                    f"KaqQuantDdbStreamWriteRepository.save2stream is occured error: tableName is {ddb_table_name} - {str(e)} - {str(traceback.format_exc())}"
                )

    def build_insert_values_fast(self, data: pd.DataFrame | list):
        if data.empty:
            return []
        dtypes = data.dtypes.tolist()
        # 提前确定哪些列需要加引号
        str_idx = {i for i, dt in enumerate(dtypes) if dt == object or dt == "object" or dt == "str"}
        # 转成 ndarray，减少 pandas 参与
        arr = data.to_numpy()

        # 使用内部函数避免lambda闭包问题，提升性能
        def format_value(i, v):
            if v is None or (isinstance(v, float) and np.isnan(v)):
                return "NULL"
            elif i in str_idx:
                return f"'{v}'"
            else:
                return str(v)

        # 使用列表推导式一次性生成所有行，避免多次append
        return ["(" + ", ".join(format_value(i, v) for i, v in enumerate(row)) + ")" for row in arr]

    def build_insert_values_fast_list(self, data: list):
        if not data:
            return []
        #
        first_row = data[0]
        str_idx = {i for i, v in enumerate(first_row) if type(v) is str}

        # 优化：使用 type() 代替 isinstance() 减少函数调用开销
        def format_value(i, v):
            if v is None:
                return "NULL"
            # 如果在字符串索引中，直接格式化（避免 isinstance）
            if i in str_idx:
                return f"'{v}'"

            # 使用 type() 比 isinstance() 更快
            v_type = type(v)
            if v_type is float:
                if np.isnan(v):
                    return "NULL"
                return str(v)
            if v_type is str:
                return f"'{v}'"  # 第一行可能是 None 导致误判
            return str(v)

        # 使用列表推导式一次性生成所有行
        return ["(" + ", ".join(format_value(i, v) for i, v in enumerate(row)) + ")" for row in data]

    def save2stream_batch(self, ddb_table_name: str, df: pd.DataFrame):
        """
        调用此方法之前, 需要将dataframe中的字符串类型的值 ，添加引号
        """
        try:
            # start1 = time.monotonic_ns()
            row = self.build_insert_values_fast(df)
            values = ", ".join(row)
            script = f"insert into {ddb_table_name} values {values}"
            # start2 = time.monotonic_ns()
            self.session.run(script, clearMemory=True)
            # end = time.monotonic_ns()
            # if "KAQ_QUANT_LOG" in os.environ:
            #     diff = end - start2
            #     if diff > 1_000_000_0:  # 超过1毫秒
            #         self.logger.warning(
            #             f"KaqQuantDdbStreamWriteRepository.save2stream_batch cost time is only write : {end - start2} ns, save2stream_batch :{end - start1} ns, batch size is {len(df)}, tableName is {ddb_table_name}"
            #         )
        except Exception as e:
            self.logger.error(
                f"KaqQuantDdbStreamWriteRepository.save2stream_batch is occured error: tableName is {ddb_table_name} - {str(e)} - {str(traceback.format_exc())}"
            )

    def save2stream_batch_list(self, ddb_table_name: str, data: list):
        """
        调用此方法之前, 需要将数组中的字符串类型的值 ，添加引号
        """
        try:
            # start1 = time.monotonic_ns()
            row = self.build_insert_values_fast_list(data)
            values = ", ".join(row)
            script = f"insert into {ddb_table_name} values {values}"
            # start2 = time.monotonic_ns()
            self.session.run(script, clearMemory=True)
            # end = time.monotonic_ns()
            # if "KAQ_QUANT_LOG" in os.environ:
            #     diff = end - start2
            #     if diff > 1_000_000_0:  # 超过1毫秒
            #         self.logger.warning(
            #             f"KaqQuantDdbStreamWriteRepository.save2stream_batch_list cost time is only write : {end - start2} ns, save2stream_batch_list :{end - start1} ns, batch size is {len(data)}, tableName is {ddb_table_name}"
            #         )
        except Exception as e:
            self.logger.error(
                f"KaqQuantDdbStreamWriteRepository.save2stream_batch_list is occured error: tableName is {ddb_table_name} - {str(e)} - {str(traceback.format_exc())}"
            )


# 方式二: 同步调用,但有python端的队列等待
class DDBAsyncDFWriter:
    def __init__(self, appender, batch_size=1000, flush_interval_ms=80):
        self.logger = get_logger()
        self.appender = appender
        self.batch_size = batch_size
        self.flush_interval = flush_interval_ms / 1000.0

        self.queue = queue.Queue(maxsize=10000)
        self.running = True

        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def add_df(self, df):
        """直接传入一个 DataFrame"""
        if not self.running:
            return
        if df is None or df.empty:
            return
        try:
            self.queue.put(df, block=False)
        except queue.Full:
            self.logger.error("Warning: DDBAsyncDFWriter queue is full!")

    def _worker(self):
        buffer = []
        current_rows = 0
        last_flush_time = time.time()

        while self.running or not self.queue.empty():
            try:
                # 使用较短的 timeout 以便能快速响应 running=False 状态
                df = self.queue.get(timeout=0.01)
                buffer.append(df)
                current_rows += len(df)
            except queue.Empty:
                # 即使没有新数据，如果已经进入停止流程且 buffer 还有数，也要处理
                if not self.running and not buffer:
                    break

            now = time.time()
            # 触发条件：行数够了，或时间到了，或者程序正在停止
            if buffer and (current_rows >= self.batch_size or (now - last_flush_time) >= self.flush_interval or not self.running):
                self._do_flush(buffer)
                buffer = []
                current_rows = 0
                last_flush_time = now

    def _do_flush(self, buffer):
        try:
            if not buffer:
                return
            final_df = pd.concat(buffer, ignore_index=True)
            self.appender.append(final_df)
        except Exception as e:
            self.logger.error(f"DolphinDB 写入异常: {e}")

    def stop(self):
        """
        优雅停止：
        1. 设置 running 为 False
        2. 等待后台线程把队列里剩余的数据全部 flush 完
        """
        self.logger.warning("正在停止 DDBAsyncDFWriter 并清空残留数据...")
        self.running = False
        self.thread.join()  # 等待工作线程处理完最后一批 buffer
        self.logger.info("DDBAsyncDFWriter 已安全停止。")


class KaqQuantDdbStreamWriteSyncRepository:
    """
    使用appender直接写入的方式
    """

    def __init__(self, host, port, user, passwd, tableName=None, batch_size=1000, flush_interval_ms=80):
        if tableName is None:
            raise ValueError(f"Error tableName, please set. tableName={tableName}")
        self.tableName = tableName
        self.logger = get_logger(self)
        """
        创建ddb连接 && 添加ddb流数据表支持
        """
        try:
            mutex.acquire()
            self.session = ddb.session()
            self.session.connect(host, port, user, passwd, tryReconnectNums=100, reconnect=True, keepAliveTime=1000, readTimeout=10, writeTimeout=5)

            self.batch_writer = DDBAsyncDFWriter(
                ddb.TableAppender(table_name=self.tableName, conn=self.session), batch_size=batch_size, flush_interval_ms=flush_interval_ms
            )
            # 需要注意的是 fetchSize 取值不能小于 8192 （记录条数）
            self.size = 8192
        except Exception as e:
            self.logger.error(f"KaqQuantDdbTableStreamWriteRepository.__init__ is occured error: {str(e)} - {str(traceback.format_exc())}")
        finally:
            mutex.release()

    # @deprecated("请确保pandas数据与ddb表的数据类型一致.")
    def insert(self, df: pd.DataFrame):
        """
        dataframe中日期等类型与ddb流表中一致,例如：
            df['create_time'] = pd.to_datetime(df['create_time'], unit='ms')
            df['event_time'] = pd.to_datetime(df['event_time'], unit='ms')
        """
        try:
            self.batch_writer.add_df(df)
        except Exception as e:
            self.logger.error(f"KaqQuantDdbTableStreamWriteRepository.insert is occured error:  {str(e)} - {str(traceback.format_exc())}")


# 方式三: 异步调用, 但属于ddb的client内部的c++多线程解析与写入，适合一条条写入
class KaqQuantDdbStreamMTWWriteRepository:
    def __init__(self, host, port, user, passwd, tableName=None, batch_size=1000, throttle=50, partitionCol="", threadCount=1):
        self.logger = get_logger(self)
        """
        创建ddb连接 && 添加ddb流数据表支持
        """
        try:
            mutex.acquire()
            self.session = ddb.session(enableASYNC=True)
            self.session.connect(host, port, user, passwd, tryReconnectNums=100, reconnect=True, keepAliveTime=1000, readTimeout=10, writeTimeout=5)
            self.batch_writer = ddb.MultithreadedTableWriter(
                host,
                port,
                user,
                passwd,
                tableName=tableName,
                dbPath="",
                batchSize=batch_size,
                throttle=throttle,
                threadCount=threadCount,
                partitionCol=partitionCol,
            )
        except Exception as e:
            self.logger.error(f"KaqQuantDdbStreamMTWWriteRepository.__init__ is occured error: {str(e)} - {str(traceback.format_exc())}")
        finally:
            mutex.release()

    def save2stream_batch(self, df: pd.DataFrame = pd.DataFrame(), cols: list = []):
        try:
            if df is None or df.empty:
                return
            if cols is None or len(cols) <= 0:
                for _, row in df.iterrows():
                    _args = row.tolist()
                    self.batch_writer.insert(*_args)
            else:
                for _, row in df.iterrows():
                    _args = [row[i] for i in cols]
                    self.batch_writer.insert(*_args)
        except Exception as e:
            self.logger.error(f"KaqQuantDdbStreamMTWWriteRepository.insert is occured error: {str(e)} - {str(traceback.format_exc())}")

    def save2stream_list(self, row: list = []):
        try:
            if row is None or len(row) <= 0:
                return
            self.batch_writer.insert(*row)
        except Exception as e:
            self.logger.error(f"KaqQuantDdbStreamMTWWriteRepository.insert is occured error: {str(e)} - {str(traceback.format_exc())}")

    def stop(self):
        """
        结束调用
        """
        self.batch_writer.waitForThreadCompletion()


if __name__ == "__main__":
    host, port, user, passwd = yml_utils.get_ddb_info(os.getcwd())
    kaq = KaqQuantDdbStreamWriteRepository(host, port, user, passwd)
