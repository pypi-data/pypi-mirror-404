import logging
from typing import Optional

from ddx.common.logging import auditor_logger
from ddx._rust.common import ProductSymbol
from ddx._rust.common.state import DerivadexSMT, Price
from ddx._rust.common.state.keys import PriceKey
from ddx._rust.decimal import Decimal
from sortedcontainers import SortedKeyList

logger = logging.getLogger(__name__)


def get_prices_for_symbol_and_duration(
    smt: DerivadexSMT,
    symbol: ProductSymbol,
    duration: int,
) -> SortedKeyList:
    """
    Get Price leaves from SMT for a given market and a certain duration. This is used
    internally when computing the funding rate since we need to
    obtain all the Price leaves in the state to derive the
    time-weighted average of the premium rate.

    Parameters
    ----------
    smt: DerivadexSMT
        DerivaDEX Sparse Merkle Tree
    symbol : ProductSymbol
        Market symbol
    duration : int
        Duration of lookback in ticks
    """
    logger.debug(f"Getting price leaves for {symbol} for the last {duration} ticks")

    price_leaves = smt.all_prices_for_symbol(symbol)
    logger.debug(f"All price leaves for {symbol}: {price_leaves}")
    if not price_leaves:
        return SortedKeyList()

    sorted_price_leaves = SortedKeyList(key=lambda price: price[1].time_value)
    for key, value in price_leaves:
        sorted_price_leaves.add((key, value))

    last_time_value = sorted_price_leaves[-1][1].time_value

    bisect_time_value = max(last_time_value - duration, 0)
    logger.debug(
        f"Retrieving price leaves from within ticks [{bisect_time_value}, {last_time_value}]"
    )
    bisect_index = sorted_price_leaves.bisect_key_left(bisect_time_value)
    logger.debug(f"Bisection index: {bisect_index}")

    return sorted_price_leaves[bisect_index:]


def get_most_recent_price(
    smt: DerivadexSMT, symbol: ProductSymbol, time_value: int
) -> Optional[tuple[PriceKey, Price]]:
    """
    Get the most recent Price leaf for a given market and time value.

    Parameters
    ----------
    smt: DerivadexSMT
        DerivaDEX Sparse Merkle Tree
    symbol : ProductSymbol
        Market symbol
    time_value : int
        Time value of reference
    """

    logger.debug(
        f"Getting the most recent price for {symbol} at time value {time_value}"
    )

    price_leaves = smt.all_prices_for_symbol(symbol)
    logger.debug(f"All price leaves for {symbol}: {price_leaves}")

    # Find the most recent price leaf at or before time_value
    return max(
        filter(lambda price: price[1].time_value <= time_value, price_leaves),
        key=lambda price: price[1].ordinal,
        default=None,
    )
