"""
InsuranceFundUpdate
"""

from attrs import define, field
from ddx.common.transactions.event import Event
from ddx._rust.common import TokenSymbol
from ddx._rust.common.state import DerivadexSMT, InsuranceFundContribution
from ddx._rust.common.state.keys import InsuranceFundContributionKey, InsuranceFundKey
from ddx._rust.common.transactions import InsuranceFundUpdateKind
from ddx._rust.decimal import Decimal


@define
class InsuranceFundUpdate(Event):
    """
    Defines an InsuranceFundUpdate

    An InsuranceFundUpdate is an update to a trader's insurance fund
    contribution (such as depositing or withdrawing
    collateral).

    Attributes:
        address (str): Trader's Ethereum address this insurance fund update belongs to
        collateral_address (str): Collateral's Ethereum address a deposit/withdrawal has been made with
        amount (Decimal): The amount of collateral deposited or withdrawn
        update_kind (InsuranceFundUpdateKind): Update kind (Deposit=0, Withdraw=1)
        tx_hash (str): The Ethereum transaction's hash
        request_index (int): Sequenced request index of transaction
    """

    address: str = field(eq=str.lower)
    collateral_address: str = field(eq=str.lower)
    amount: Decimal
    update_kind: InsuranceFundUpdateKind
    tx_hash: str = field(eq=str.lower)
    request_index: int = field(default=-1, eq=False)

    @classmethod
    def decode_value_into_cls(cls, raw_tx_log_event: dict):
        """
        Decode a raw transaction log event (dict) into an
        InsuranceFundUpdate instance.

        Parameters
        ----------
        raw_tx_log_event : dict
            Raw transaction log event being processed
        """

        insurance_fund_update_tx_event = raw_tx_log_event["event"]["c"]

        return cls(
            insurance_fund_update_tx_event["address"],
            insurance_fund_update_tx_event["collateralAddress"],
            Decimal(insurance_fund_update_tx_event["amount"]),
            InsuranceFundUpdateKind(insurance_fund_update_tx_event["updateKind"]),
            insurance_fund_update_tx_event["txHash"],
            raw_tx_log_event["requestIndex"],
        )

    def process_tx(
        self,
        smt: DerivadexSMT,
        **kwargs,
    ):
        """
        Process an InsuranceFundUpdate transaction. An
        InsuranceFundUpdate consists of information relating to updates
        for a trader's insurance fund contribution, such
        as when their free or frozen balance has changed due to a
        deposit or withdrawal. This will update the
        InsuranceFundContribution leaf in the SMT.

        Parameters
        ----------
        smt: DerivadexSMT
            DerivaDEX Sparse Merkle Tree
        **kwargs
            Additional args specific to InsuranceFundUpdate transactions
        """

        insurance_fund_contribution_key: InsuranceFundContributionKey = (
            InsuranceFundContributionKey(self.address)
        )
        insurance_fund_contribution = smt.insurance_fund_contribution(
            insurance_fund_contribution_key
        )

        symbol = TokenSymbol.from_address(self.collateral_address)
        if self.update_kind == InsuranceFundUpdateKind.Deposit:
            # If InsuranceFundUpdate is of deposit type

            if insurance_fund_contribution is None:
                # If we haven't yet seen the InsuranceFundContribution
                # leaf, create a new one
                insurance_fund_contribution = InsuranceFundContribution.default()

            # Adjust the existing strategy leaf by incrementing the
            # free collateral by the amount in the deposit event
            insurance_fund_contribution.set_avail_balance(
                symbol,
                insurance_fund_contribution.avail_balance[symbol] + self.amount,
            )

            insurance_fund_key: InsuranceFundKey = InsuranceFundKey()
            insurance_fund = smt.insurance_fund(insurance_fund_key)

            insurance_fund[symbol] += self.amount

            # Update the SMT with the H256 repr of the key and the
            # InsuranceFundContribution leaf
            smt.store_insurance_fund_contribution(
                insurance_fund_contribution_key, insurance_fund_contribution
            )
            smt.store_insurance_fund(insurance_fund_key, insurance_fund)
        elif self.update_kind == InsuranceFundUpdateKind.Withdraw:
            # If InsuranceFundUpdate is of withdrawal (claimed) type
            if (
                insurance_fund_contribution is None
                or insurance_fund_contribution.locked_balance[symbol] < self.amount
            ):
                raise Exception(
                    "InsuranceFundContribution leaf either non-existent or insufficiently capitalized to facilitate withdrawal"
                )

            # Adjust the existing InsuranceFundContribution leaf by decrementing the
            # locked balance by the amount in the withdrawal event
            insurance_fund_contribution.set_locked_balance(
                symbol,
                insurance_fund_contribution.locked_balance[symbol] - self.amount,
            )

            # Update the SMT with the H256 repr of the key and the
            # Strategy leaf
            smt.store_insurance_fund_contribution(
                insurance_fund_contribution_key, insurance_fund_contribution
            )
