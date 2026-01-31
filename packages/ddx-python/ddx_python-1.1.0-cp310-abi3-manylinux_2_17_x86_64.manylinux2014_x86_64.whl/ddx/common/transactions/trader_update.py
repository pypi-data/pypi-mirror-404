"""
Trader Update module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common.state import DerivadexSMT, Trader
from ddx._rust.common.state.keys import TraderKey
from ddx._rust.common.transactions import TraderUpdateKind
from ddx._rust.decimal import Decimal
from typing import Optional


def _is_zero_address(addr: Optional[str]) -> bool:
    if addr is None:
        return True
    try:
        return int(str(addr).replace("0x", ""), 16) == 0
    except Exception:
        return False


@define
class TraderUpdate(Event):
    """
    Defines a TraderUpdate

    A TraderUpdate is an update to a trader's DDX account (such as depositing
    or withdrawing DDX).

    Attributes:
        trader_address (str): Trader's Ethereum address this strategy belongs to
        amount (Decimal): The amount of collateral deposited or withdrawn
        update_kind (TraderUpdateKind): Update kind (Deposit, Withdraw, Profile)
        pay_fees_in_ddx (bool): Whether trader has opted to pay fees in DDX by default
        referral_address (Optional[str]): Optional referral address to set exactly once
        tx_hash (str): The Ethereum transaction's hash
        request_index (int): Sequenced request index of transaction
    """

    trader_address: str = field(eq=str.lower)
    amount: Decimal
    update_kind: TraderUpdateKind
    pay_fees_in_ddx: bool
    referral_address: Optional[str] = None
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a StrategyUpdate
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        trader_update_tx_event = raw_tx_log_event["event"]["c"]

        amount_raw = trader_update_tx_event.get("amount")
        amount = Decimal(amount_raw) if amount_raw is not None else Decimal("0")

        return cls(
            trader_update_tx_event["trader"],
            amount,
            TraderUpdateKind(trader_update_tx_event["updateKind"]),
            trader_update_tx_event.get("payFeesInDdx", False),
            trader_update_tx_event.get("referralAddress"),
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a TraderUpdate transaction. A TraderUpdate consists
        of information relating to updates to a trader. This will
        update the Trader leaf in the SMT.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to TraderUpdate transactions
        """

        trader_key: TraderKey = TraderKey(self.trader_address)
        trader = smt.trader(trader_key)

        if self.update_kind == TraderUpdateKind.DepositDDX:
            # If TraderUpdate is of deposit type
            if trader is None:
                # Initialize a new Trader Leaf
                trader = Trader.default()

            trader.avail_ddx_balance += self.amount
        elif self.update_kind == TraderUpdateKind.WithdrawDDX:
            # If TraderUpdate is of withdrawal (claimed) type
            if trader is None or trader.locked_ddx_balance < self.amount:
                raise Exception(
                    "Trader leaf either non-existent or insufficiently capitalized to facilitate withdrawal"
                )

            # Adjust the existing Trader leaf by decrementing the
            # free collateral by the amount in the withdrawal event
            trader.locked_ddx_balance -= self.amount
        elif self.update_kind == TraderUpdateKind.Profile:
            # If TraderUpdate is of profile type
            if trader is None:
                raise Exception("Trader leaf non-existent")

            # Adjust the existing Trader leaf by setting the
            # flag to pay fees in DDX
            trader.pay_fees_in_ddx = self.pay_fees_in_ddx
            if self.referral_address and not _is_zero_address(self.referral_address):
                # Set-once semantics: only set when currently unset/zero.
                if _is_zero_address(trader.referral_address):
                    # Ensure the referral uses the 21-byte TraderAddress format (chain byte + EOA).
                    referral = self.referral_address
                    if referral.startswith("0x") and len(referral) == 42:
                        referral = f"0x00{referral[2:]}"
                    trader.referral_address = referral
                elif trader.referral_address != self.referral_address:
                    raise Exception("Referral address already set for trader")

        smt.store_trader(trader_key, trader)
