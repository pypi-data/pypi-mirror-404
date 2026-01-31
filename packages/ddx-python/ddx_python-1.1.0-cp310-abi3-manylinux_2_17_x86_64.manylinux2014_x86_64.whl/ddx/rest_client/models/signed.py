from typing import Optional, Dict, Union, Any, Literal
from ddx.models.base import CamelModel, HexStr
from pydantic import Field, field_validator, ConfigDict
from ddx._rust.common.requests import SafetyFailure


class SequencedReceiptContent(CamelModel):
    """Content of a successful sequenced receipt."""

    nonce: HexStr
    request_hash: HexStr
    request_index: int = Field(..., ge=0)
    sender: HexStr
    enclave_signature: HexStr


class ErrorReceiptContent(CamelModel):
    """Content of an error receipt."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    message: str
    inner: SafetyFailure

    @field_validator("inner", mode="before")
    def _parse_safety_failure(cls, v):
        if isinstance(v, SafetyFailure):
            return v
        return SafetyFailure[v] if isinstance(v, str) else SafetyFailure(v)


class TradeReceipt(CamelModel):
    """Model for trade request receipts."""

    t: Literal["Sequenced", "SafetyFailure"]
    c: Union[SequencedReceiptContent, ErrorReceiptContent, Dict[str, Any]]

    @property
    def is_success(self) -> bool:
        """Check if the receipt indicates success."""

        return self.t == "Sequenced"

    @property
    def is_error(self) -> bool:
        """Check if the receipt indicates an error."""

        return self.t in ("Error", "SafetyFailure")

    @property
    def error_message(self) -> Optional[str]:
        """Get the error message if this is an error receipt."""

        if self.is_error and isinstance(self.c, ErrorReceiptContent):
            return self.c.message
        return None

    @property
    def error(self) -> Optional[SafetyFailure]:
        if self.is_error and isinstance(self.c, ErrorReceiptContent):
            return self.c.inner
        return None
