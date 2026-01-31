from typing import Optional

from kaq_quant_common.api.rest.instruction.models import (
    InstructionRequestBase, InstructionResponseBase)

# -----------------------------借贷-------------------


# ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ 活期借币
class QueryFlexibleLoanAssetRequest(InstructionRequestBase):
    # 币种代码
    coin: str

class QueryFlexibleLoanAssetResponse(InstructionResponseBase):
    # 币种代码
    coin: str
    # 活期借币利率
    interestRate: Optional[float] = None
    # 最低可借数量
    minLimit: Optional[float] = None
    # 最高可借数量
    maxLimit: Optional[float] = None
