from enum import Enum


class System(str, Enum):
    """Enum containing all system-related endpoint paths."""

    GET_EXCHANGE_INFO = "/exchange/api/v1/exchange_info"
    GET_CONNECTION_INFO = "/exchange/api/v1/ping"
    GET_SYMBOLS = "/exchange/api/v1/symbols"
    GET_SERVER_TIME = "/exchange/api/v1/time"
    GET_COLLATERAL_AGGREGATION = "/stats/api/v1/aggregations/collateral"
    GET_DDX_AGGREGATION = "/stats/api/v1/aggregations/ddx"
    GET_INSURANCE_FUND_AGGREGATION = "/stats/api/v1/aggregations/insurance_fund"
    GET_EPOCH_HISTORY = "/stats/api/v1/epochs"
    GET_INSURANCE_FUND_HISTORY = "/stats/api/v1/insurance_fund"
    GET_SPECS = "/stats/api/v1/specs"
    GET_EXCHANGE_STATUS = "/stats/api/v1/status"
    GET_DDX_SUPPLY = "/stats/api/v1/supply"
    GET_TRADABLE_PRODUCTS = "/stats/api/v1/tradable_products"

    GET_DEPLOYMENT_INFO = "/contract-server/addresses"


class Trade(str, Enum):
    """Enum containing all trade-related endpoint paths."""

    GET_STRATEGY_FEES_HISTORY = "/stats/api/v1/fees"
    GET_STRATEGY_POSITIONS = "/stats/api/v1/positions"
    GET_STRATEGY = "/stats/api/v1/strategy"
    GET_STRATEGIES = "/stats/api/v1/strategies"
    GET_STRATEGY_METRICS = "/stats/api/v1/strategy_metrics"
    GET_TRADER = "/stats/api/v1/trader"


class Market(str, Enum):
    """Enum containing all market-related endpoint paths."""

    GET_MARK_PRICE_HISTORY = "/exchange/api/v1/mark_prices"
    GET_ORDER_BOOK_L3 = "/exchange/api/v1/order_book"
    GET_ORDER_UPDATE_HISTORY = "/exchange/api/v1/order_updates"
    GET_STRATEGY_UPDATE_HISTORY = "/exchange/api/v1/strategy_updates"
    GET_TICKERS = "/exchange/api/v1/tickers"
    GET_TRADER_UPDATE_HISTORY = "/exchange/api/v1/trader_updates"
    GET_BALANCE_AGGREGATION = "/stats/api/v1/aggregations/balance"
    GET_FEES_AGGREGATION = "/stats/api/v1/aggregations/fees"
    GET_FUNDING_RATE_COMPARISON_AGGREGATION = "/stats/api/v1/aggregations/funding_rate_comparison"
    GET_TOP_TRADERS_AGGREGATION = "/stats/api/v1/aggregations/traders"
    GET_VOLUME_AGGREGATION = "/stats/api/v1/aggregations/volume"
    GET_FUNDING_RATE_HISTORY = "/stats/api/v1/funding_rate_history"
    GET_OPEN_INTEREST_HISTORY = "/stats/api/v1/open_interest_history"
    GET_ORDER_BOOK_L2 = "/stats/api/v1/order_book_l2"
    GET_PRICE_CHECKPOINT_HISTORY = "/stats/api/v1/price_checkpoints"


class Signed(str, Enum):
    """Enum containing all signed endpoint paths."""

    ENCRYPTION_KEY = "/v2/encryption-key"
    SUBMIT_REQUEST = "/v2/request"


class OnChain(str, Enum):
    """Enum containing all on-chain-related endpoint paths."""

    KYC_AUTH = "/kyc/v1/kyc-auth"
    PROOF = "/v2/proof"
