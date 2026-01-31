from datetime import datetime
from typing import List, Optional
from pydantic import Field, ConfigDict, field_validator
from ddx.models.base import CamelModel


class SettlementInfo(CamelModel):
    """Settlement information model."""

    type: str
    duration_value: str
    duration_unit: str


class SymbolInfo(CamelModel):
    """Symbol information model."""

    symbol: str
    tick_size: str
    max_order_notional: str
    max_taker_price_deviation: str
    min_order_size: str
    kind: str  # SingleNamePerpetual, IndexFundPerpetual, FixedExpiryFuture


class ExchangeInfo(CamelModel):
    """Exchange information model."""

    settlements_info: List[SettlementInfo]
    assets: List[str]
    symbols: List[SymbolInfo]


class ExchangeInfoResponse(CamelModel):
    """Response model for exchange info endpoint."""

    value: ExchangeInfo
    success: bool
    timestamp: int


class PingResponse(CamelModel):
    """Response model for ping endpoint."""

    model_config = CamelModel.model_config | ConfigDict(extra="allow")

    # The ping endpoint returns an empty object on success
    # We'll allow extra fields in case the response changes in the future


class Symbol(CamelModel):
    """Tradable product symbol model."""

    kind: int  # 0: Perpetual Market, 2: Index Market, 4: Futures Market
    symbol: str
    name: str
    is_active: bool
    created_at: datetime


class SymbolsResponse(CamelModel):
    """Response model for symbols endpoint."""

    value: List[Symbol]
    success: bool
    timestamp: int


class ServerTimeResponse(CamelModel):
    """Response model for server time endpoint."""

    server_time: int


class Epoch(CamelModel):
    """Epoch data model."""

    epoch_id: int
    start_time: datetime
    end_time: Optional[datetime] = None


class EpochHistoryResponse(CamelModel):
    """Response model for epoch history endpoint."""

    value: List[Epoch]
    success: bool
    timestamp: int


class InsuranceFund(CamelModel):
    """Insurance fund update data model."""

    epoch_id: int
    tx_ordinal: int
    symbol: str
    total_capitalization: Optional[str] = None
    kind: int  # 0: fill, 1: liquidation, 2: deposit, 3: withdrawal
    created_at: datetime


class InsuranceFundHistoryResponse(CamelModel):
    """Response model for insurance fund history endpoint with cursor pagination."""

    value: List[InsuranceFund]
    next_epoch: Optional[int] = Field(None, ge=0)
    next_tx_ordinal: Optional[int] = Field(None, ge=0)
    next_ordinal: Optional[int] = Field(None, ge=0)
    success: bool
    timestamp: int


class SpecValue(CamelModel):
    """Spec value model."""

    model_config = CamelModel.model_config | ConfigDict(extra="allow")

    # This is a flexible model that can contain various fields
    # based on the kind of spec


class Spec(CamelModel):
    """Spec data model."""

    kind: int = Field(..., description="0: Market, 1: SpotGateway")
    name: str
    expr: str
    value: Optional[SpecValue] = None


class SpecsResponse(CamelModel):
    """Response model for specs endpoint."""

    value: List[Spec]
    success: bool
    timestamp: int


class OnChainCheckpoint(CamelModel):
    """On-chain checkpoint information model."""

    latest_on_chain_checkpoint: int
    latest_checkpoint_transaction_link: Optional[str] = None


class ExchangeStatus(CamelModel):
    """Exchange status information model."""

    current_epoch: str
    latest_on_chain_checkpoint: Optional[OnChainCheckpoint] = None
    active_addresses: str


class ExchangeStatusResponse(CamelModel):
    """Response model for exchange status endpoint."""

    value: ExchangeStatus
    success: bool
    timestamp: int


class DDXSupply(CamelModel):
    """DDX supply information model."""

    circulating_supply: str


class DDXSupplyResponse(CamelModel):
    """Response model for DDX supply endpoint."""

    value: DDXSupply
    success: bool
    timestamp: int


class TradableProduct(CamelModel):
    """Tradable product data model."""

    kind: int  # 0: Perpetual Market, 2: Index Market, 4: Futures Market
    symbol: str
    name: str
    is_active: bool
    created_at: datetime


class TradableProductsResponse(CamelModel):
    """Response model for tradable products endpoint."""

    value: List[TradableProduct]
    success: bool
    timestamp: int


class CollateralAggregation(CamelModel):
    """Collateral aggregation data model."""

    model_config = CamelModel.model_config | ConfigDict(extra="allow")

    timestamp: int
    # Dynamic fields will be handled with extra='allow'
    # Fields like collateral_deposits, collateral_withdrawals, etc.

    # Add method to access dynamic fields
    def get_value(self, field_name: str) -> Optional[str]:
        """Get value for a specific collateral field."""
        return getattr(self, f"collateral_{field_name}", None)


class CollateralAggregationResponse(CamelModel):
    """Response model for collateral aggregation endpoint."""

    value: List[CollateralAggregation]
    next_starting_value: Optional[str] = None
    success: bool
    timestamp: int


class DDXAggregation(CamelModel):
    """DDX aggregation data model."""

    model_config = CamelModel.model_config | ConfigDict(extra="allow")

    timestamp: int
    # Dynamic fields will be available through extra="allow"
    # Fields like ddx_deposits, ddx_withdrawals, etc.

    # Add method to get DDX value by type
    def get_ddx_value(self, value_type: str) -> Optional[str]:
        """Get DDX value for a specific type."""
        return getattr(self, f"ddx_{value_type}", None)


class DDXAggregationResponse(CamelModel):
    """Response model for DDX aggregation endpoint."""

    value: List[DDXAggregation]
    next_starting_value: Optional[str] = None
    success: bool
    timestamp: int


class InsuranceFundAggregation(CamelModel):
    """Insurance fund aggregation data model."""

    model_config = CamelModel.model_config | ConfigDict(extra="allow")

    timestamp: int
    # Dynamic fields will be handled with extra='allow'
    # Fields like insurance-fund_fees, insurance-fund_overall, etc.

    def get_value(self, field: str) -> Optional[str]:
        """Get a specific field value."""
        return getattr(self, field, None)


class InsuranceFundAggregationResponse(CamelModel):
    """Response model for insurance fund aggregation endpoint."""

    value: List[InsuranceFundAggregation]
    next_starting_value: Optional[str] = None
    success: bool
    timestamp: int


class DeploymentAddresses(CamelModel):
    """Model for contract deployment addresses."""

    ddx_address: str
    ddx_wallet_cloneable_address: str
    derivadex_address: str = Field(alias="derivaDEXAddress")  # Custom alias
    di_fund_token_factory_address: str
    governance_address: str
    governance_dip12_address: str
    gas_consumer_address: str
    insurance_fund_address: str
    pause_address: str
    trader_address: str
    usdt_address: str
    ausdt_address: str
    cusdt_address: str
    usdc_address: str
    cusdc_address: str
    ausdc_address: str
    husd_address: str
    gusd_address: str
    gnosis_safe_address: str
    gnosis_safe_proxy_factory_address: str
    gnosis_safe_proxy_address: str
    create_call_address: str
    banner_address: str
    funded_insurance_fund_address: str
    funded_insurance_fund_dip12_address: str
    checkpoint_address: str
    registration_address: str
    initialize_app_address: str
    specs_address: str
    collateral_address: str
    collateral_dip12_address: str
    custodian_address: str
    reject_address: str
    stake_address: str
    stake_dip12_address: str
    pilot_reset_address: str


class DeploymentInfo(CamelModel):
    """Model for deployment information."""

    addresses: DeploymentAddresses
    chain_id: int
    eth_rpc_url: str
