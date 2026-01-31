from attrs import define, field
from ddx._rust.decimal import Decimal


@define
class TradeMiningParams:
    """
    Defines the trade mining parameters determined at the start of a scenario
    """

    trade_mining_length: int
    trade_mining_reward_per_epoch: Decimal
    trade_mining_maker_reward_percentage: Decimal
    trade_mining_taker_reward_percentage: Decimal = field(init=False)

    def __attrs_post_init__(self):
        self.trade_mining_taker_reward_percentage = (
            Decimal("1") - self.trade_mining_maker_reward_percentage
        )
