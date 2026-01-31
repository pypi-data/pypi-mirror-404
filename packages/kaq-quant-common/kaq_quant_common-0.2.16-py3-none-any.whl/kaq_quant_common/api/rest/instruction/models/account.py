from enum import Enum
from typing import Optional

from pydantic import BaseModel

from . import InstructionRequestBase, InstructionResponseBase


# 资产信息
class AssetsInfo(BaseModel):
    # 币种
    coin: str
    # 余额
    balance: float


# ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ 查询合约账户余额
class ContractBalanceRequest(InstructionRequestBase):
    # 币种
    coin: Optional[str] = None


class ContractBalanceResponse(InstructionResponseBase):
    #
    assets: list[AssetsInfo]


# ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ 查询账户损益资金流水
class AccountIncomeInfo(BaseModel):
    symbol: str
    incomeType: int
    income: float
    time: int
    subType: Optional[str] = None


class AccountIncomeRequest(InstructionRequestBase):
    # 交易对
    symbol: Optional[str] = None
    # 收益类型
    incomeType: Optional[int] = None
    # 起始时间
    startTime: Optional[int] = None
    # 结束时间
    endTime: Optional[int] = None


class AccountIncomeResponse(InstructionResponseBase):
    income_list: list[AccountIncomeInfo]
