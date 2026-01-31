from attrs import define
from ddx._rust.common import ProductSymbol
from ddx._rust.common.requests import SettlementAction


@define
class EpochParams:
    """
    Defines the epoch parameters
    """

    epoch_size: int
    price_checkpoint_size: int
    settlement_epoch_length: int
    pnl_realization_period: int
    funding_period: int
    trade_mining_period: int
    expiry_price_leaves_duration: int

    @property
    def settlement_action_periods(self):
        res = {
            SettlementAction.TradeMining: self.trade_mining_period,
            SettlementAction.PnlRealization: self.pnl_realization_period,
            SettlementAction.FundingDistribution: self.funding_period,
        }

        return res
