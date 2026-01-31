"""
PriceCheckpoint module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common import ProductSymbol
from ddx._rust.common.accounting import MarkPriceMetadata
from ddx._rust.common.state import DerivadexSMT, Price
from ddx._rust.common.state.keys import PriceKey
from ddx._rust.decimal import Decimal


@define(hash=True)
class PriceCheckpoint(Event):
    """
    Defines a PriceCheckpoint

    A PriceCheckpoint is when a market registers an update to the
    composite index price a perpetual is tracking along with the mark
    price metadata component.

    Attributes:
        symbol (ProductSymbol): The symbol for the market this price update is for.
        mark_price_metadata (MarkPriceMetadata): Mark price metadata used for calculating mark price
        index_price_hash (str): Index price hash
        index_price (Decimal): Composite index price (a weighted average across several oracle sources)
        ordinal (int): The numerical sequence-identifying value for a PriceCheckpoint
        time_value (int): Time value
        request_index (int): Sequenced request index of transaction
    """

    symbol: ProductSymbol
    mark_price_metadata: MarkPriceMetadata = field(hash=False)
    index_price_hash: str = field(eq=str.lower)
    index_price: Decimal = field(hash=False)
    ordinal: int = field(hash=False)
    time_value: int
    request_index: int = field(default=-1, eq=False, hash=False)

    def is_void(self):
        return self.index_price == Decimal("0")

    @property
    def mark_price(self) -> Decimal:
        if isinstance(self.mark_price_metadata, MarkPriceMetadata.Ema):
            mark_price = min(
                self.index_price * Decimal("1.005"),
                max(
                    self.index_price * Decimal("0.995"),
                    self.index_price + self.mark_price_metadata.ema,
                ),
            ).recorded_amount()
        elif (
            isinstance(self.mark_price_metadata,
                       MarkPriceMetadata.Average) is not None
        ):
            mark_price = (self.index_price + self.mark_price_metadata.accum) / (
                self.mark_price_metadata.count + 1
            )
        else:
            raise ValueError("Invalid MarkPriceMetadata type")
        return mark_price.recorded_amount()

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a PriceCheckpoint transaction. A PriceCheckpoint
        consists of information relating to a new price checkpoint,
        such as the symbol, composite index price, and mark price
        metadata. This will update the Price leaf in the SMT.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to PriceCheckpoint transactions
        """
        price_key = PriceKey(self.symbol, self.index_price_hash)
        price = Price(
            self.index_price,
            self.mark_price_metadata,
            self.ordinal,
            self.time_value,
        )
        smt.store_price(price_key, price)

        # Update latest price leaves abstraction with the new price
        # checkpoint data
        kwargs["latest_price_leaves"][self.symbol] = (
            price_key,
            price,
        )
