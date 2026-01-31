"""
Utils module
"""

from decimal import Decimal as PyDecimal
import simplejson as json

from ddx._rust.common.enums import OrderSide
from ddx._rust.decimal import Decimal


def round_to_unit(val: Decimal) -> Decimal:
    """
    Round a decimal value down to 6 units of precision.

    Parameters
    ----------
    val : Decimal
        Value to be rounded
    """

    return val.quantize(6)


def to_base_unit_amount(val: Decimal, decimals: int) -> int:
    """
    Convert a value to grains format (e.g. DDX grains would be
    multiplying by 10 ** 18).

    Parameters
    ----------
    val : Decimal
        Value to be scaled up
    decimals : int
        Number of decimal places to scale up to
    """

    return int(round_to_unit(val) * 10**decimals)


def to_unit_amount(val: int, decimals: int) -> Decimal:
    """
    Convert a value from grains format (e.g. from DDX grains would be
    dividing by 10 ** 18).

    Parameters
    ----------
    val : Decimal
        Value to be scaled down
    decimals : int
        Number of decimal places to scale down by
    """

    return Decimal(str(val)) / 10**decimals


def to_base_unit_amount_list(vals: list[Decimal], decimals: int) -> list[int]:
    """
    Convert values to grains format (e.g. DDX grains would be
    multiplying by 10 ** 18).

    Parameters
    ----------
    vals : list[Decimal]
        Values to be scaled up
    decimals : int
        Number of decimal places to scale up to
    """

    return [to_base_unit_amount(val, decimals) for val in vals]


def to_unit_amount_list(vals: list[int], decimals: int):
    """
    Convert values from grains format (e.g. from DDX grains would be
    dividing by 10 ** 18).

    Parameters
    ----------
    vals : list[int]
        Values to be scaled down
    decimals : int
        Number of decimal places to scale down by
    """

    return [to_unit_amount(val, decimals) for val in vals]


def to_adjusted_encoding_for_negative_val(val: int):
    """
    Adjust encoding for a potentially negative value

    Parameters
    ----------
    vals : int
        Values to be adjusted
    """

    return 16**32 + abs(val) if val < 0 else val


def to_adjusted_encoding_for_negative_val_list(vals: list[int]):
    """
    Adjust encoding for list of potentially negative values

    Parameters
    ----------
    vals : list[int]
        list of values to be adjusted
    """

    return [to_adjusted_encoding_for_negative_val(val) for val in vals]


def from_adjusted_encoding_for_negative_val(val: int):
    """
    Adjust encoding for a potentially negative value

    Parameters
    ----------
    vals : int
        Values to be adjusted
    """

    return val if val < 16**32 else -(val - 16**32)


def get_parsed_tx_log_entry(tx_log_entry: dict):
    """
    Parse an individual transaction log entry into a format
    suitable for the Auditor. This format was selected so
    that the Auditor can be reused as-is by the integration
    tests with no changes needed.

    Parameters
    ----------
    tx_log_entry : dict
        Transaction log message
    """
    return {
        "event": tx_log_entry["event"],
        "requestIndex": int(tx_log_entry["requestIndex"]),
        "epochId": int(tx_log_entry["epochId"]),
        "txOrdinal": int(tx_log_entry["ordinal"]),
        "batchId": int(tx_log_entry["batchId"]),
        "timeValue": int(tx_log_entry["time"]["value"]),
        "timestamp": int(tx_log_entry["time"]["timestamp"]),
        "stateRootHash": tx_log_entry["stateRootHash"],
    }


def calculate_max_collateral(
    collateral_tranches: list[tuple[Decimal, Decimal]], ddx_balance: Decimal
) -> Decimal:
    limit = Decimal("0")
    for ddx_threshold, max_collateral in collateral_tranches:
        limit = max_collateral
        if ddx_balance < ddx_threshold:
            break
    return limit


class ComplexOutputEncoder(json.JSONEncoder):
    """
    Custom JSON-encoder for serializing objects
    """

    def __init__(self, **kwargs):
        super(ComplexOutputEncoder, self).__init__(**kwargs)

    def default(self, o):
        if hasattr(o, "repr_json"):
            return o.repr_json()
        elif type(o) == Decimal:
            return PyDecimal(str(o))
        return json.JSONEncoder.default(self, o)
