from typing import Optional, Type, TypeVar, Callable
import asyncio
import threading
import time

import requests
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    
from kaq_quant_common.api.common.auth import get_auth_token
from kaq_quant_common.utils import logger_utils
from pydantic import BaseModel

R = TypeVar("R", bound=BaseModel)


class ApiClientBase:
    """
    api 客户端
    """
    
    # 类级别的共享 event loop 线程
    _shared_loop: Optional[asyncio.AbstractEventLoop] = None
    _shared_loop_thread: Optional[threading.Thread] = None
    _loop_lock = threading.Lock()

    def __init__(self, base_url: str, token: Optional[str] = None):
        self._base_url = base_url.rstrip("/")
        self._token = token if token is not None else get_auth_token()
        self._logger = logger_utils.get_logger(self)
        # 异步客户端（懒加载）
        self._async_client: Optional[httpx.AsyncClient] = None

    @classmethod
    def _ensure_shared_loop(cls):
        """确保共享的 event loop 已创建并运行"""
        if cls._shared_loop is None or not cls._shared_loop.is_running():
            with cls._loop_lock:
                # 双重检查
                if cls._shared_loop is None or not cls._shared_loop.is_running():
                    def run_loop():
                        """在后台线程中运行 event loop"""
                        cls._shared_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(cls._shared_loop)
                        cls._shared_loop.run_forever()
                    
                    cls._shared_loop_thread = threading.Thread(
                        target=run_loop,
                        daemon=True,
                        name="ApiClient-EventLoop"
                    )
                    cls._shared_loop_thread.start()
                    
                    # 等待 loop 启动
                    while cls._shared_loop is None:
                        time.sleep(0.01)

    # 发送请求
    def _make_request(self, method_name: str, request_data: BaseModel, response_model: Type[R]) -> R:
        url = f"{self._base_url}/api/{method_name}"
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            # 发送post请求
            response = requests.post(url, json=request_data.model_dump(), headers=headers or None)
            # 检查响应状态码，如果不成功，则尝试解析错误信息并抛出异常
            if not response.ok:
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", response.text)
                except ValueError:
                    error_message = response.text
                raise requests.exceptions.HTTPError(f"HTTP error occurred: {response.status_code} - {error_message}", response=response)
            # 返回请求结果
            return response_model(**response.json())
        except requests.exceptions.RequestException as e:
            self._logger.error(f"An error occurred: {e}")
            raise

    # 异步发送请求
    async def _make_request_async(self, method_name: str, request_data: BaseModel, response_model: Type[R]) -> R:
        """
        异步发送请求
        
        Args:
            method_name: API方法名
            request_data: 请求数据
            response_model: 响应模型
            
        Returns:
            响应对象
        """
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx library is required for async requests. Install it with: pip install httpx")
        
        url = f"{self._base_url}/api/{method_name}"
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        
        # 懒加载创建async client
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=30.0)
        
        try:
            # 发送异步post请求
            response = await self._async_client.post(
                url, 
                json=request_data.model_dump(), 
                headers=headers or None
            )
            # 检查响应状态码
            if not response.is_success:
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", response.text)
                except ValueError:
                    error_message = response.text
                raise httpx.HTTPStatusError(
                    f"HTTP error occurred: {response.status_code} - {error_message}",
                    request=response.request,
                    response=response
                )
            # 返回请求结果
            return response_model(**response.json())
        except httpx.HTTPStatusError:
            raise
        except Exception as e:
            self._logger.error(f"An error occurred: {e}")
            raise

    # 回调方式发送请求
    def _make_request_callback(
        self, 
        method_name: str, 
        request_data: BaseModel, 
        response_model: Type[R],
        on_success: Optional[Callable[[R], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """
        回调方式发送请求，使用共享的 event loop
        
        Args:
            method_name: API方法名
            request_data: 请求数据
            response_model: 响应模型
            on_success: 成功回调，接收响应对象，可选
            on_error: 错误回调，接收异常对象，可选
        """
        # 确保共享 loop 已启动
        self._ensure_shared_loop()
        
        async def _async_task():
            """异步任务"""
            try:
                result = await self._make_request_async(method_name, request_data, response_model)
                # 调用成功回调（如果提供）
                if on_success:
                    on_success(result)
            except Exception as e:
                # 调用错误回调
                if on_error:
                    on_error(e)
                else:
                    self._logger.error(f"Callback request failed: {e}")
        
        # 将任务提交到共享的 event loop
        asyncio.run_coroutine_threadsafe(_async_task(), self._shared_loop)
    
    async def close_async(self):
        """关闭异步客户端连接"""
        if self._async_client is not None:
            await self._async_client.aclose()
            self._async_client = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_async()
