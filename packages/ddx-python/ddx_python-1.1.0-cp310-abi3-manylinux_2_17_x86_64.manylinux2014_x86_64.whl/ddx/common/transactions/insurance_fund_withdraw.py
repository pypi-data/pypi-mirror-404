"""
InsuranceFundWithdraw module
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common import TokenSymbol
from ddx._rust.common.state import DerivadexSMT, InsuranceFundContribution
from ddx._rust.common.state.keys import InsuranceFundContributionKey, InsuranceFundKey
from ddx._rust.decimal import Decimal


@define
class InsuranceFundWithdraw(Event):
    """
    Defines an InsuranceFundWithdraw Update

    An InsuranceFundWithdraw is when a withdrawal of collateral is **signaled**.

    Attributes:
        recipient_address (str): Trader address DDX is being withdrawn to
        amount (Decimal): The amount of DDX being withdrawn
        request_index (int): Sequenced request index of transaction
    """

    recipient_address: str = field(eq=str.lower)
    currency: str = field(eq=str.lower)
    amount: Decimal
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into a Withdraw
        instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        insurance_fund_withdraw_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            insurance_fund_withdraw_tx_event["recipientAddress"],
            insurance_fund_withdraw_tx_event["currency"],
            Decimal(insurance_fund_withdraw_tx_event["amount"]),
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process a Withdraw transaction. A Withdraw event consists
        of consists of information relating to withdrawal of collateral.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to InsuranceFundWithdraw transactions
        """

        insurance_fund_key: InsuranceFundKey = InsuranceFundKey()
        insurance_fund = smt.insurance_fund(insurance_fund_key)

        contributor_key: InsuranceFundContributionKey = InsuranceFundContributionKey(
            self.recipient_address
        )
        contributor: InsuranceFundContribution = smt.insurance_fund_contribution(
            contributor_key
        )

        # Decrement the free balance by the withdrawn amount
        symbol = TokenSymbol.from_address(self.currency)
        contributor.set_avail_balance(
            symbol,
            contributor.avail_balance[symbol] - self.amount,
        )

        # Increment the frozen balance by the withdrawn amount
        contributor.set_locked_balance(
            symbol,
            contributor.locked_balance[symbol] + self.amount,
        )

        # Update the SMT with the H256 repr of the key and
        # the InsuranceFundContribution leaf for the signer
        smt.store_insurance_fund_contribution(contributor_key, contributor)

        insurance_fund[symbol] -= self.amount

        # Update the SMT with the H256 repr of the key and the
        # Strategy leaf
        smt.store_insurance_fund(insurance_fund_key, insurance_fund)
