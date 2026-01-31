# 定义 服务器api
import time
from abc import ABC, abstractmethod

from kaq_quant_common.api.common.api_interface import ApiInterface, api_method
from kaq_quant_common.api.rest.api_server_base import ApiServerBase
from kaq_quant_common.api.rest.instruction.helper.order_helper import \
    OrderHelper
from kaq_quant_common.api.rest.instruction.helper.mock_order_helper import \
    MockOrderHelper
from kaq_quant_common.api.rest.instruction.helper.commission_helper import \
    CommissionHelper
from kaq_quant_common.api.rest.instruction.models import \
    InstructionResponseBase
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
    QueryOpenInterestRequest, QueryOpenInterestResponse)
from kaq_quant_common.api.rest.instruction.models.transfer import (
    TransferRequest, TransferResponse)
from kaq_quant_common.resources.kaq_mysql_resources import \
    KaqQuantMysqlRepository
from kaq_quant_common.resources.kaq_redis_resources import \
    KaqQuantRedisRepository


class InstructionServerBase(ApiServerBase, ApiInterface, ABC):

    def __init__(self, exchange="", host="0.0.0.0", port=5000):
        super().__init__(self, host, port)
        #
        self._mysql: KaqQuantMysqlRepository = None
        self._redis: KaqQuantRedisRepository = None
        # 交易所
        self._exchange = exchange

        # helper
        self._order_helper = OrderHelper(self)
        self._mock_order_helper = MockOrderHelper(self)
        self._commission_helper = CommissionHelper(self)

    # 统一处理返回数据
    def _wrap_response(self, rsp: InstructionResponseBase):
        if rsp is not None:
            # 时间
            if rsp.event_time is None:
                rsp.event_time = int(time.time() * 1000)
        return rsp

    # 下单
    @api_method(OrderRequest, OrderResponse)
    def order(self, request: OrderRequest) -> OrderResponse:
        ret = self._on_order(request)
        if len(ret.orders) == 1 and ret.orders[0].message is not None:
            # 只有一笔订单，而且失败了，抛出异常
            raise Exception(f"order failed: {ret.orders[0].message}")
        return ret

    # 模拟下单
    @api_method(OrderRequest, OrderResponse)
    def mock_order(self, request: OrderRequest) -> OrderResponse:
        """
        模拟下单，不调用真实交易所API
        直接在父类处理，子类无需重写
        """
        ret = OrderResponse(orders=[])
        
        # 遍历所有订单
        for order in request.orders:
            # 获取模拟成交价
            mock_fill_price = order.current_price
            
            # 从commission_helper获取手续费率，如果获取失败使用默认值0.0005
            mock_fee_rate = self._commission_helper.get_taker_commission_rate(
                symbol=order.symbol,
                default_rate=0.0005
            )
            
            # 使用mock_order_helper处理
            try:
                self._mock_order_helper.process_order(
                    order=order,
                    mock_fill_price=mock_fill_price,
                    mock_fee_rate=mock_fee_rate
                )
                # 成功的订单
                from kaq_quant_common.api.rest.instruction.models.order import OpenedOrderInfo
                ret.orders.append(
                    OpenedOrderInfo(
                        order_id=order.order_id,
                        symbol=order.symbol
                    )
                )
            except Exception as e:
                self._logger.error(f"Mock order failed: {e}")
                from kaq_quant_common.api.rest.instruction.models.order import OpenedOrderInfo
                ret.orders.append(
                    OpenedOrderInfo(
                        order_id=order.order_id,
                        symbol=order.symbol,
                        message=str(e)
                    )
                )
        
        return ret

    # 修改订单
    @api_method(ModifyOrderRequest, ModifyOrderResponse)
    def modify_order(self, request: ModifyOrderRequest) -> ModifyOrderResponse:
        return self._on_modify_order(request)

    # 取消订单
    @api_method(CancelOrderRequest, CancelOrderResponse)
    def cancel_order(self, request: CancelOrderRequest) -> CancelOrderResponse:
        return self._on_cancel_order(request)

    # 查询当前全部挂单
    @api_method(AllOpenOrdersRequest, AllOpenOrdersResponse)
    def all_open_orders(self, request: AllOpenOrdersRequest) -> AllOpenOrdersResponse:
        return self._on_all_open_orders(request)

    # 查询交易对设置
    @api_method(QuerySymbolConfigRequest, QuerySymbolConfigResponse)
    def query_symbol_config(self, request: QuerySymbolConfigRequest) -> QuerySymbolConfigResponse:
        return self._on_query_symbol_config(request)

    # 调整杠杆
    @api_method(ChangeLeverageRequest, ChangeLeverageResponse)
    def change_leverage(self, request: ChangeLeverageRequest) -> ChangeLeverageResponse:
        return self._on_change_leverage(request)

    # 划转
    @api_method(TransferRequest, TransferResponse)
    def transfer(self, request: TransferRequest) -> TransferResponse:
        return self._on_transfer(request)

    # 查询合约账户余额
    @api_method(ContractBalanceRequest, ContractBalanceResponse)
    def contract_balance(self, request: ContractBalanceRequest) -> ContractBalanceResponse:
        return self._on_contract_balance(request)
    
    # 查询5档深度
    @api_method(LimitOrderBookRequest, LimitOrderBookResponse)
    def get_limit_order(self, request: LimitOrderBookRequest) -> LimitOrderBookResponse:
        return self._on_get_limit_order(request)
    
    # 查询账户损益资金流水
    @api_method(AccountIncomeRequest, AccountIncomeResponse)
    def get_account_income(self, request: AccountIncomeRequest) -> AccountIncomeResponse:
        return self._on_get_account_income(request)
    
    # 查询未平仓合约数量
    @api_method(QueryOpenInterestRequest, QueryOpenInterestResponse)
    def query_open_interest(self, request: QueryOpenInterestRequest) -> QueryOpenInterestResponse:
        return self._on_query_open_interest(request)

    # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ abstract methods

    @abstractmethod
    def _on_order(self, request: OrderRequest) -> OrderResponse:
        pass

    @abstractmethod
    def _on_modify_order(self, request: ModifyOrderRequest) -> ModifyOrderResponse:
        pass

    @abstractmethod
    def _on_cancel_order(self, request: CancelOrderRequest) -> CancelOrderResponse:
        pass

    @abstractmethod
    def _on_all_open_orders(self, request: AllOpenOrdersRequest) -> AllOpenOrdersResponse:
        pass

    @abstractmethod
    def _on_query_symbol_config(self, request: QuerySymbolConfigRequest) -> QuerySymbolConfigResponse:
        pass

    @abstractmethod
    def _on_change_leverage(self, request: ChangeLeverageRequest) -> ChangeLeverageResponse:
        pass

    @abstractmethod
    def _on_transfer(self, request: TransferRequest) -> TransferResponse:
        pass

    @abstractmethod
    def _on_contract_balance(self, request: ContractBalanceRequest) -> ContractBalanceResponse:
        pass

    @abstractmethod
    def _on_get_limit_order(self, request: LimitOrderBookRequest) -> LimitOrderBookResponse:
        pass

    @abstractmethod
    def _on_get_account_income(self, request: AccountIncomeRequest) -> AccountIncomeResponse:
        pass

    @abstractmethod
    def _on_query_open_interest(self, request: QueryOpenInterestRequest) -> QueryOpenInterestResponse:
        pass