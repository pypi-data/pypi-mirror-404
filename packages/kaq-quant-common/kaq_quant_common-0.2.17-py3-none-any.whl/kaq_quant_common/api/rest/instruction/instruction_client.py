# 定义 客户端
import time
from typing import Type, TypeVar, Callable, Optional

from kaq_quant_common.api.rest.api_client_base import ApiClientBase
from kaq_quant_common.api.rest.instruction.models import (
    InstructionRequestBase, InstructionResponseBase)
from kaq_quant_common.api.rest.instruction.models.account import (
    AccountIncomeRequest, AccountIncomeResponse, ContractBalanceRequest,
    ContractBalanceResponse)
from kaq_quant_common.api.rest.instruction.models.order import (
    AllOpenOrdersRequest, AllOpenOrdersResponse, CancelOrderRequest,
    CancelOrderResponse, ChangeLeverageRequest, ChangeLeverageResponse,
    LimitOrderBookRequest, LimitOrderBookResponse, ModifyOrderRequest,
    ModifyOrderResponse, OrderRequest, OrderResponse, QuerySymbolConfigRequest,
    QuerySymbolConfigResponse)
from kaq_quant_common.api.rest.instruction.models.position import (
    QueryOpenInterestRequest, QueryOpenInterestResponse, QueryPositionRequest,
    QueryPositionResponse)
from kaq_quant_common.api.rest.instruction.models.transfer import (
    TransferRequest, TransferResponse)
from kaq_quant_common.utils import uuid_utils

R = TypeVar("R", bound=InstructionResponseBase)


class InstructionClient(ApiClientBase):

    # 重写一下make_request处理公用字段
    def _make_request(self, method: str, request: InstructionRequestBase, response_model: Type[R]) -> R:
        # 处理公用字段
        # 时间
        if request.event_time is None:
            request.event_time = int(time.time() * 1000)
        # TODO 任务id
        if request.task_id is None:
            request.task_id = f"t_{uuid_utils.generate_uuid()}"
        return super()._make_request(method, request, response_model)

    # 下单
    def order(self, request: OrderRequest) -> OrderResponse:
        return self._make_request("order", request, OrderResponse)

    # 模拟下单
    def mock_order(self, request: OrderRequest) -> OrderResponse:
        return self._make_request("mock_order", request, OrderResponse)

    # 修改订单
    def modify_order(self, request: ModifyOrderRequest) -> ModifyOrderResponse:
        return self._make_request("modify_order", request, ModifyOrderResponse)

    # 取消订单
    def cancel_order(self, request: CancelOrderRequest) -> CancelOrderResponse:
        return self._make_request("cancel_order", request, CancelOrderResponse)

    # 查询当前全部挂单
    def all_open_orders(self, request: AllOpenOrdersRequest) -> AllOpenOrdersResponse:
        return self._make_request("all_open_orders", request, AllOpenOrdersResponse)

    # 查询交易对设置
    def query_symbol_config(self, request: QuerySymbolConfigRequest) -> QuerySymbolConfigResponse:
        return self._make_request("query_symbol_config", request, QuerySymbolConfigResponse)

    # 调整杠杆
    def change_leverage(self, request: ChangeLeverageRequest) -> ChangeLeverageResponse:
        return self._make_request("change_leverage", request, ChangeLeverageResponse)

    # 查询持仓
    def query_position(self, request: QueryPositionRequest) -> QueryPositionResponse:
        return self._make_request("query_position", request, QueryPositionResponse)

    # 划转
    def transfer(self, request: TransferRequest) -> TransferResponse:
        return self._make_request("transfer", request, TransferResponse)

    # 查询合约账户余额
    def contract_balance(self, request: ContractBalanceRequest) -> ContractBalanceResponse:
        return self._make_request("contract_balance", request, ContractBalanceResponse)
    
    # 查询5档深度
    def get_limit_order(self, request: LimitOrderBookRequest) -> LimitOrderBookResponse:
        return self._make_request("get_limit_order", request, LimitOrderBookResponse)

    # 查询账户损益资金流水
    def get_account_income(self, request: AccountIncomeRequest) -> AccountIncomeResponse:
        return self._make_request("get_account_income", request, AccountIncomeResponse)

    # 查询未平仓合约数量
    def query_open_interest(self, request: QueryOpenInterestRequest) -> QueryOpenInterestResponse:
        return self._make_request("query_open_interest", request, QueryOpenInterestResponse)

    # ==================== 异步方法 ====================
    
    async def _make_request_async(self, method: str, request: InstructionRequestBase, response_model: Type[R]) -> R:
        """异步版本的_make_request，处理公用字段"""
        # 处理公用字段
        if request.event_time is None:
            request.event_time = int(time.time() * 1000)
        if request.task_id is None:
            request.task_id = f"t_{uuid_utils.generate_uuid()}"
        return await super()._make_request_async(method, request, response_model)
    
    # 异步下单
    async def order_async(self, request: OrderRequest) -> OrderResponse:
        return await self._make_request_async("order", request, OrderResponse)
    
    # 异步模拟下单
    async def mock_order_async(self, request: OrderRequest) -> OrderResponse:
        return await self._make_request_async("mock_order", request, OrderResponse)
    
    # 异步修改订单
    async def modify_order_async(self, request: ModifyOrderRequest) -> ModifyOrderResponse:
        return await self._make_request_async("modify_order", request, ModifyOrderResponse)
    
    # 异步取消订单
    async def cancel_order_async(self, request: CancelOrderRequest) -> CancelOrderResponse:
        return await self._make_request_async("cancel_order", request, CancelOrderResponse)
    
    # 异步查询当前全部挂单
    async def all_open_orders_async(self, request: AllOpenOrdersRequest) -> AllOpenOrdersResponse:
        return await self._make_request_async("all_open_orders", request, AllOpenOrdersResponse)
    
    # 异步查询交易对设置
    async def query_symbol_config_async(self, request: QuerySymbolConfigRequest) -> QuerySymbolConfigResponse:
        return await self._make_request_async("query_symbol_config", request, QuerySymbolConfigResponse)
    
    # 异步调整杠杆
    async def change_leverage_async(self, request: ChangeLeverageRequest) -> ChangeLeverageResponse:
        return await self._make_request_async("change_leverage", request, ChangeLeverageResponse)
    
    # 异步查询持仓
    async def query_position_async(self, request: QueryPositionRequest) -> QueryPositionResponse:
        return await self._make_request_async("query_position", request, QueryPositionResponse)
    
    # 异步划转
    async def transfer_async(self, request: TransferRequest) -> TransferResponse:
        return await self._make_request_async("transfer", request, TransferResponse)
    
    # 异步查询合约账户余额
    async def contract_balance_async(self, request: ContractBalanceRequest) -> ContractBalanceResponse:
        return await self._make_request_async("contract_balance", request, ContractBalanceResponse)
    
    # 异步查询5档深度
    async def get_limit_order_async(self, request: LimitOrderBookRequest) -> LimitOrderBookResponse:
        return await self._make_request_async("get_limit_order", request, LimitOrderBookResponse)
    
    # 异步查询账户损益资金流水
    async def get_account_income_async(self, request: AccountIncomeRequest) -> AccountIncomeResponse:
        return await self._make_request_async("get_account_income", request, AccountIncomeResponse)
    
    # 异步查询未平仓合约数量
    async def query_open_interest_async(self, request: QueryOpenInterestRequest) -> QueryOpenInterestResponse:
        return await self._make_request_async("query_open_interest", request, QueryOpenInterestResponse)

    # ==================== 回调方法 ====================
    
    def _make_request_callback(
        self, 
        method: str, 
        request: InstructionRequestBase, 
        response_model: Type[R],
        on_success: Optional[Callable[[R], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """回调版本的_make_request，处理公用字段"""
        # 处理公用字段
        if request.event_time is None:
            request.event_time = int(time.time() * 1000)
        if request.task_id is None:
            request.task_id = f"t_{uuid_utils.generate_uuid()}"
        super()._make_request_callback(method, request, response_model, on_success, on_error)
    
    # 回调下单
    def order_callback(
        self, 
        request: OrderRequest, 
        on_success: Optional[Callable[[OrderResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("order", request, OrderResponse, on_success, on_error)
    
    # 回调模拟下单
    def mock_order_callback(
        self, 
        request: OrderRequest, 
        on_success: Optional[Callable[[OrderResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("mock_order", request, OrderResponse, on_success, on_error)
    
    # 回调修改订单
    def modify_order_callback(
        self, 
        request: ModifyOrderRequest, 
        on_success: Optional[Callable[[ModifyOrderResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("modify_order", request, ModifyOrderResponse, on_success, on_error)
    
    # 回调取消订单
    def cancel_order_callback(
        self, 
        request: CancelOrderRequest, 
        on_success: Optional[Callable[[CancelOrderResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("cancel_order", request, CancelOrderResponse, on_success, on_error)
    
    # 回调查询当前全部挂单
    def all_open_orders_callback(
        self, 
        request: AllOpenOrdersRequest, 
        on_success: Optional[Callable[[AllOpenOrdersResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("all_open_orders", request, AllOpenOrdersResponse, on_success, on_error)
    
    # 回调查询交易对设置
    def query_symbol_config_callback(
        self, 
        request: QuerySymbolConfigRequest, 
        on_success: Optional[Callable[[QuerySymbolConfigResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("query_symbol_config", request, QuerySymbolConfigResponse, on_success, on_error)
    
    # 回调调整杠杆
    def change_leverage_callback(
        self, 
        request: ChangeLeverageRequest, 
        on_success: Optional[Callable[[ChangeLeverageResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("change_leverage", request, ChangeLeverageResponse, on_success, on_error)
    
    # 回调查询持仓
    def query_position_callback(
        self, 
        request: QueryPositionRequest, 
        on_success: Optional[Callable[[QueryPositionResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("query_position", request, QueryPositionResponse, on_success, on_error)
    
    # 回调划转
    def transfer_callback(
        self, 
        request: TransferRequest, 
        on_success: Optional[Callable[[TransferResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("transfer", request, TransferResponse, on_success, on_error)
    
    # 回调查询合约账户余额
    def contract_balance_callback(
        self, 
        request: ContractBalanceRequest, 
        on_success: Optional[Callable[[ContractBalanceResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("contract_balance", request, ContractBalanceResponse, on_success, on_error)
    
    # 回调查询5档深度
    def get_limit_order_callback(
        self, 
        request: LimitOrderBookRequest, 
        on_success: Optional[Callable[[LimitOrderBookResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("get_limit_order", request, LimitOrderBookResponse, on_success, on_error)
    
    # 回调查询账户损益资金流水
    def get_account_income_callback(
        self, 
        request: AccountIncomeRequest, 
        on_success: Optional[Callable[[AccountIncomeResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("get_account_income", request, AccountIncomeResponse, on_success, on_error)
    
    # 回调查询未平仓合约数量
    def query_open_interest_callback(
        self, 
        request: QueryOpenInterestRequest, 
        on_success: Optional[Callable[[QueryOpenInterestResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        self._make_request_callback("query_open_interest", request, QueryOpenInterestResponse, on_success, on_error)