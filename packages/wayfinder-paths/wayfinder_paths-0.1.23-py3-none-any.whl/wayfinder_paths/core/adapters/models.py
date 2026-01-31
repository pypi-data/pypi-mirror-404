from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class OperationBase(BaseModel):
    adapter: str
    transaction_hash: str | None
    transaction_chain_id: int | None


class SWAP(OperationBase):
    type: Literal["SWAP"] = "SWAP"
    from_token_id: str
    to_token_id: str
    from_amount: str
    to_amount: str
    from_amount_usd: float
    to_amount_usd: float
    transaction_status: str | None = None
    transaction_receipt: dict[str, Any] | None = None


class LEND(OperationBase):
    type: Literal["LEND"] = "LEND"
    contract: str
    amount: int


class UNLEND(OperationBase):
    type: Literal["UNLEND"] = "UNLEND"
    contract: str
    amount: int


# Type alias for operation types (currently only SWAP is used)
Operation = SWAP | LEND | UNLEND


class STRAT_OP(BaseModel):
    op_data: Annotated[Operation, Field(discriminator="type")]
