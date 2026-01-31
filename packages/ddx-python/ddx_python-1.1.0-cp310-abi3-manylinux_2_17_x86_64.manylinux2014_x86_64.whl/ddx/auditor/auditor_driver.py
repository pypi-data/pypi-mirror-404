"""
AuditorDriver module
"""

import asyncio
import datetime
from collections import defaultdict
from collections.abc import AsyncIterable
from typing import Optional, Type, TypeVar
import os
import requests
import simplejson as json
import websockets
from websockets import WebSocketClientProtocol
from web3.auto import w3

from ddx._rust.common import ProductSymbol
from ddx._rust.common.state import DerivadexSMT, Item, ItemKind, Price
from ddx._rust.common.state.keys import (
    BookOrderKey,
    InsuranceFundKey,
    PositionKey,
    PriceKey,
    StrategyKey,
    TraderKey,
)
from ddx._rust.decimal import Decimal
from ddx._rust.h256 import H256

from ddx.common.epoch_params import EpochParams
from ddx.common.logging import CHECKMARK, auditor_logger
from ddx.common.trade_mining_params import TradeMiningParams
from ddx.common.transactions.advance_epoch import AdvanceEpoch
from ddx.common.transactions.advance_settlement_epoch import AdvanceSettlementEpoch
from ddx.common.transactions.all_price_checkpoints import AllPriceCheckpoints
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.cancel_all import CancelAll
from ddx.common.transactions.complete_fill import CompleteFill
from ddx.common.transactions.disaster_recovery import DisasterRecovery
from ddx.common.transactions.event import Event
from ddx.common.transactions.fee_distribution import FeeDistribution
from ddx.common.transactions.funding import Funding
from ddx.common.transactions.futures_expiry import FuturesExpiry
from ddx.common.transactions.genesis import Genesis
from ddx.common.transactions.insurance_fund_update import InsuranceFundUpdate
from ddx.common.transactions.insurance_fund_withdraw import InsuranceFundWithdraw
from ddx.common.transactions.liquidation import Liquidation
from ddx.common.transactions.partial_fill import PartialFill
from ddx.common.transactions.pnl_realization import PnlRealization
from ddx.common.transactions.post_order import PostOrder
from ddx.common.transactions.signer_registered import SignerRegistered
from ddx.common.transactions.specs_update import SpecsUpdate
from ddx.common.transactions.strategy_update import StrategyUpdate
from ddx.common.transactions.tradable_product_update import TradableProductUpdate
from ddx.common.transactions.trade_mining import TradeMining
from ddx.common.transactions.trader_update import TraderUpdate
from ddx.common.transactions.withdraw import Withdraw
from ddx.common.transactions.withdraw_ddx import WithdrawDDX
from ddx.common.utils import get_parsed_tx_log_entry, ComplexOutputEncoder
from ddx.auditor.websocket_message import WebsocketEventType, WebsocketMessage


logger = auditor_logger(__name__)

EventT = TypeVar("EventT", bound=Event)
RAW_TYPE_TO_EVENT_TYPE: dict[str, Type[EventT]] = {
    "Post": PostOrder,
    "CompleteFill": CompleteFill,
    "PartialFill": PartialFill,
    "Liquidation": Liquidation,
    "Cancel": Cancel,
    "CancelAll": CancelAll,
    "StrategyUpdate": StrategyUpdate,
    "TraderUpdate": TraderUpdate,
    "PriceCheckpoint": AllPriceCheckpoints,
    "PnlRealization": PnlRealization,
    "Funding": Funding,
    "FuturesExpiry": FuturesExpiry,
    "TradeMining": TradeMining,
    "Withdraw": Withdraw,
    "WithdrawDDX": WithdrawDDX,
    "InsuranceFundWithdraw": InsuranceFundWithdraw,
    "Genesis": Genesis,
    "AdvanceEpoch": AdvanceEpoch,
    "AdvanceSettlementEpoch": AdvanceSettlementEpoch,
    "InsuranceFundUpdate": InsuranceFundUpdate,
    "DisasterRecovery": DisasterRecovery,
    "FeeDistribution": FeeDistribution,
    "SignerRegistered": SignerRegistered,
    "SpecsUpdate": SpecsUpdate,
    "TradableProductUpdate": TradableProductUpdate,
}


def empty_queue(q: asyncio.Queue):
    for _ in range(q.qsize()):
        # Depending on your program, you may want to
        # catch QueueEmpty
        q.get_nowait()
        q.task_done()


class AuditorDriver:
    """
    Defines an AuditorDriver.
    """

    def __init__(
        self,
        webserver_url: str,
        genesis_params: dict,
        epoch_params: EpochParams,
        trade_mining_params: TradeMiningParams,
        collateral_tranches: list[tuple[Decimal, Decimal]],
        contract_deployment: str,
    ):
        """
        Initialize an AuditorDriver. An Auditor allows any third-party to
        process a state snapshot of the DerivaDEX Sparse Merkle Tree (SMT)
        and transaction log entries to validate the integrity of the
        exchange. The driver essentially maintains its own SMT and can
        transition its state upon receiving transaction log entries. The
        root hashes must match.

        Parameters
        ----------
        webserver_url: str
            Operator hostname
        epoch_params: EpochParams
            Epoch parameters
        collateral_tranches: list[tuple[Decimal, Decimal]]
            Collateral guards tranches
        genesis_params : dict
            Genesis params for the environment
        contract_deployment: str
            Contract deployment name, e.g. geth
        """

        self.webserver_url = webserver_url
        self.contract_deployment = contract_deployment
        self.epoch_params = epoch_params
        self.trade_mining_params = trade_mining_params
        self.collateral_tranches = collateral_tranches
        self.genesis_params = genesis_params

    def _reset(self):
        # Initialize an empty SMT
        self.smt = DerivadexSMT()

        # Initialize latest price leaves. These
        # technically are abstractions above the SMT for easier/faster
        # access for a trader client
        self.latest_price_leaves: dict[ProductSymbol, tuple[PriceKey, Price]] = {}

        # Initialize a data construct for pending transaction log
        # entries. We maintain a backlog of pending transaction log entries
        # in this scenario so that although we may receive transaction log
        # entries out of order, we will always apply them to the SMT in order.
        self.pending_tx_log_entries = defaultdict(dict)

        # Current root hash derived locally. For every transaction event
        # emitted by the transaction log, the state root hash prior to
        # the transaction being applied. As such, we maintain the
        # current root hash to compare against the next inbound
        # transaction log's root hash.
        self.current_state_root_hash = (
            "0x0000000000000000000000000000000000000000000000000000000000000000"
        )
        self.current_batch_state_root_hash = (
            "0x0000000000000000000000000000000000000000000000000000000000000000"
        )

        self.first_head = True
        self._snapshot_received = False

        # More Pythonic ask-for-forgiveness approaches for the queues
        # and event below

        # set up an asyncio queue for messages that will be added by
        # the Auditor and popped to send to the API
        try:
            empty_queue(self.api_auditor_queue)
        except AttributeError:
            self.api_auditor_queue = asyncio.Queue()

        self.expected_epoch_id = 0
        self.expected_tx_ordinal = 0
        self.latest_batch_id = 0

        self.is_trade_mining = (
            lambda epoch_id: epoch_id * self.epoch_params.epoch_size
            < self.trade_mining_params.trade_mining_length
            * self.epoch_params.trade_mining_period
            + 1
        )

    @property
    def smt(self):
        return self._smt

    @smt.setter
    def smt(self, smt):
        self._smt = smt

    @property
    def expected_epoch_id(self):
        return self._expected_epoch_id

    @expected_epoch_id.setter
    def expected_epoch_id(self, epoch_id):
        self._expected_epoch_id = epoch_id

    @property
    def expected_tx_ordinal(self):
        return self._expected_tx_ordinal

    @expected_tx_ordinal.setter
    def expected_tx_ordinal(self, tx_ordinal):
        self._expected_tx_ordinal = tx_ordinal

    def process_tx(self, tx: Event, tx_log_event: dict):
        """
        Process an individual transaction. This transaction will be
        appropriately decoded into the correct Transaction type and
        handled different to adjust the SMT.

        Parameters
        ----------
        tx : EventT
            A transaction
        """

        if isinstance(tx, PostOrder):
            # PostOrder transaction
            tx.process_tx(
                self.smt,
                latest_price_leaves=self.latest_price_leaves,
            )
        elif isinstance(tx, CompleteFill):
            # CompleteFill transaction
            tx.process_tx(
                self.smt,
                latest_price_leaves=self.latest_price_leaves,
                trade_mining_active=self.is_trade_mining(tx_log_event["epochId"]),
                epoch_id=tx_log_event["epochId"],
            )
        elif isinstance(tx, PartialFill):
            # PartialFill transaction
            tx.process_tx(
                self.smt,
                latest_price_leaves=self.latest_price_leaves,
                trade_mining_active=self.is_trade_mining(tx_log_event["epochId"]),
                epoch_id=tx_log_event["epochId"],
            )
        elif isinstance(tx, Liquidation):
            # Liquidation transaction
            tx.process_tx(
                self.smt,
                latest_price_leaves=self.latest_price_leaves,
                trade_mining_active=self.is_trade_mining(tx_log_event["epochId"]),
                epoch_id=tx_log_event["epochId"],
            )
        elif isinstance(tx, Cancel):
            # Cancel transaction
            tx.process_tx(
                self.smt,
            )
        elif isinstance(tx, CancelAll):
            # CancelAll transaction
            tx.process_tx(
                self.smt,
            )
        elif isinstance(tx, StrategyUpdate):
            # StrategyUpdate transaction
            tx.process_tx(
                self.smt,
                collateral_tranches=self.collateral_tranches,
            )
        elif isinstance(tx, TraderUpdate):
            # TraderUpdate transaction
            tx.process_tx(
                self.smt,
            )
        elif isinstance(tx, AllPriceCheckpoints):
            # AllPriceCheckpoints transaction
            tx.process_tx(
                self.smt,
                latest_price_leaves=self.latest_price_leaves,
            )
        elif isinstance(tx, PnlRealization):
            # PnlRealization transaction
            tx.process_tx(
                self.smt,
                latest_price_leaves=self.latest_price_leaves,
            )
        elif isinstance(tx, Funding):
            # Funding transaction
            tx.process_tx(
                self.smt,
                latest_price_leaves=self.latest_price_leaves,
                funding_period=self.epoch_params.funding_period,
            )
        elif isinstance(tx, FuturesExpiry):
            # FuturesExpiry transaction
            tx.process_tx(
                self.smt,
                latest_price_leaves=self.latest_price_leaves,
            )
        elif isinstance(tx, TradeMining):
            # TradeMining transaction
            tx.process_tx(
                self.smt,
                trade_mining_active=self.is_trade_mining(tx_log_event["epochId"]),
                trade_mining_reward_per_epoch=self.trade_mining_params.trade_mining_reward_per_epoch,
                trade_mining_maker_reward_percentage=self.trade_mining_params.trade_mining_maker_reward_percentage,
                trade_mining_taker_reward_percentage=self.trade_mining_params.trade_mining_taker_reward_percentage,
            )
        elif isinstance(tx, Withdraw):
            # Withdraw transaction
            tx.process_tx(
                self.smt,
            )
        elif isinstance(tx, WithdrawDDX):
            # WithdrawDDX transaction
            tx.process_tx(
                self.smt,
            )
        elif isinstance(tx, InsuranceFundWithdraw):
            # InsuranceFundWithdraw transaction
            tx.process_tx(
                self.smt,
            )
        elif isinstance(tx, Genesis):
            # Genesis transaction
            tx.process_tx(
                auditor_instance=self,
                expected_epoch_id=AuditorDriver.expected_epoch_id.fset,
                expected_tx_ordinal=AuditorDriver.expected_tx_ordinal.fset,
                smt=AuditorDriver.smt.fset,
                genesis_params=self.genesis_params,
                current_time=datetime.datetime.fromtimestamp(
                    tx_log_event["timestamp"] / 1000, tz=datetime.timezone.utc
                ),
            )
        elif isinstance(tx, AdvanceEpoch):
            # AdvanceEpoch transaction
            tx.process_tx(
                self.smt,
                auditor_instance=self,
                expected_epoch_id=AuditorDriver.expected_epoch_id.fset,
                expected_tx_ordinal=AuditorDriver.expected_tx_ordinal.fset,
            )
        elif isinstance(tx, AdvanceSettlementEpoch):
            # AdvanceSettlementEpoch transaction
            tx.process_tx(
                self.smt,
                latest_price_leaves=self.latest_price_leaves,
            )
        elif isinstance(tx, InsuranceFundUpdate):
            # InsuranceFundUpdate transaction
            tx.process_tx(
                self.smt,
            )
        elif isinstance(tx, DisasterRecovery):
            # DisasterRecovery transaction
            tx.process_tx(
                self.smt,
                latest_price_leaves=self.latest_price_leaves,
            )
        elif isinstance(tx, FeeDistribution):
            # FeeDistribution transaction
            tx.process_tx(
                self.smt,
            )
        elif isinstance(tx, SignerRegistered):
            # SignerRegistered transaction
            tx.process_tx(
                self.smt,
            )
        elif isinstance(tx, SpecsUpdate):
            # SpecsUpdate transaction
            tx.process_tx(
                self.smt,
            )
        elif isinstance(tx, TradableProductUpdate):
            # TradableProductUpdate transaction
            tx.process_tx(
                self.smt,
            )
        else:
            raise RuntimeError("Unhandled SMT transaction type: " + type(tx))

    def process_tx_log_event(
        self, tx_log_event: dict, suppress_trader_queue: bool
    ) -> list:
        """
        Process an individual transaction log entry. Each entry will be
        appropriately decoded into the correct Transaction type and
        handled differently to adjust the SMT.

        Parameters
        ----------
        tx_log_event : dict
            A transaction log event
        suppress_trader_queue : bool
            Suppress trader queue messages
        """

        processed_txs = []
        # Add the transaction log event to the pending transaction log
        # entries to be processed either now or later
        self.pending_tx_log_entries[tx_log_event["epochId"]][
            tx_log_event["txOrdinal"]
        ] = tx_log_event

        # Loop through all the pending transaction log entries that
        # should be processed now given the expected epoch ID and
        # transaction ordinal
        while (
            self.expected_epoch_id in self.pending_tx_log_entries
            and self.expected_tx_ordinal
            in self.pending_tx_log_entries[self.expected_epoch_id]
        ):
            # Retrieve the transaction log entry event that should be
            # processed now
            tx_log_event = self.pending_tx_log_entries[self.expected_epoch_id].pop(
                self.expected_tx_ordinal
            )

            def decode_tx():
                event_type = tx_log_event["event"]["t"]
                if event_type == "EpochMarker":
                    event_type = tx_log_event["event"]["c"]["kind"]
                return event_type, RAW_TYPE_TO_EVENT_TYPE[event_type].decode_value_into_cls(
                    tx_log_event
                )

            if (
                tx_log_event["batchId"] == self.latest_batch_id
                and tx_log_event["stateRootHash"] != self.current_batch_state_root_hash
            ):
                raise RuntimeError(
                    f"Tx log root hash ({tx_log_event['stateRootHash']}) != current batch root hash ({self.current_batch_state_root_hash}"
                )
            elif (
                tx_log_event["batchId"] != self.latest_batch_id
                and tx_log_event["stateRootHash"] != self.current_state_root_hash
            ):
                logger.info("state root mismatch detected - shutting down operators")
                if self.contract_deployment == "geth":
                    self.shutdown_operators()

                logger.error(
                    f"smt leaves before request {tx_log_event['requestIndex']} (result of request {tx_log_event['requestIndex'] - 1}, dump THIS request from the operator): {[(str(key), value.abi_encoded_value().hex()) for key, value in self.smt.all_leaves()]}\n\nHuman readable:\n{str(self.smt.all_leaves())}"
                )
                try:
                    req_idx = tx_log_event.get("requestIndex", "unknown")
                    dump_path = f"/tmp/auditor_mismatch_request_{req_idx}.json"
                    dump_payload = {
                        "requestIndex": req_idx,
                        "currentStateRootHash": self.current_state_root_hash,
                        "txLogStateRootHash": tx_log_event.get("stateRootHash"),
                        "txLogEvent": tx_log_event,
                        "auditorLeaves": {
                            str(key): "0x" + value.abi_encoded_value().hex()
                            for key, value in self.smt.all_leaves()
                        },
                    }
                    with open(dump_path, "w") as f:
                        json.dump(dump_payload, f, cls=ComplexOutputEncoder)
                    logger.error("wrote auditor mismatch dump to %s", dump_path)
                except Exception as e:
                    logger.error("failed to write auditor mismatch dump: %s", e)

                raise RuntimeError(
                    f"Tx log root hash ({tx_log_event['stateRootHash']}) != current root hash ({self.current_state_root_hash}"
                )

            # Extract the transaction type from the event (e.g. Post,
            # CompleteFill, etc.)
            tx_type, tx = decode_tx()

            logger.success(
                f"{CHECKMARK} - processing ({tx_type}; tx log root hash ({tx_log_event['stateRootHash']}) == current root hash ({self.current_state_root_hash}; tx ({tx_log_event})"
            )

            self.process_tx(tx, tx_log_event)

            # set the current state root hash locally
            self.current_state_root_hash = f"0x{self.smt.root().as_bytes().hex()}"

            if self.latest_batch_id != tx_log_event["batchId"]:
                self.current_batch_state_root_hash = tx_log_event["stateRootHash"]
                self.latest_batch_id = tx_log_event["batchId"]

            # Increment the expected transaction ordinal by 1 (will be
            # reset back to 0 only when the epoch advances)
            self.expected_tx_ordinal += 1
            logger.success(
                f"{CHECKMARK * 2} - processed {tx_type}; arrived at new state root hash ({self.current_state_root_hash})"
            )

            processed_txs.append(tx)

        return processed_txs

    def process_state_snapshot(
        self, expected_epoch_id: int, state_snapshot: dict
    ) -> None:
        """
        Process a state snapshot and initialize the SMT accordingly.

        Parameters
        ----------
        expected_epoch_id : int
            Expected epoch ID for incoming transactions after the
            state snapshot
        state_snapshot : dict
            The state snapshot structured as a dictionary with the
            format: {<hash(leaf_key, leaf_value)>, (leaf_key, leaf_value)}
        """

        # Loop through state snapshot dictionary items
        for state_snapshot_key, state_snapshot_value in state_snapshot.items():
            # Compute the first and second words since with these two
            # blocks of data, we can determine what type of leaf we are
            # dealing with

            state_snapshot_key = bytes.fromhex(state_snapshot_key[2:])
            # Peel the item discriminant off (the first byte of the
            # leaf key) to determine what kind of leaf it is
            item_discriminant = ItemKind(w3.to_int(state_snapshot_key[:1]))

            item = Item.abi_decode_value_into_item(
                item_discriminant, bytes.fromhex(state_snapshot_value[2:])
            )

            state_snapshot_key_h256 = H256.from_bytes(state_snapshot_key)
            self.smt.store_item_by_key(state_snapshot_key_h256, item)

            if item_discriminant == ItemKind.Price:
                # Update latest price leaves abstraction with the new
                # price checkpoint data
                price_key = PriceKey.decode_key(state_snapshot_key_h256)
                price_item = Price.from_item(item)
                # Derive the Price encoded key and H256
                # repr
                if (
                    price_key.symbol not in self.latest_price_leaves
                    or price_item.ordinal
                    > self.latest_price_leaves[price_key.symbol][1].ordinal
                ):
                    self.latest_price_leaves[price_key.symbol] = (
                        price_key,
                        price_item,
                    )

        self.expected_epoch_id = expected_epoch_id
        self.expected_tx_ordinal = 0

    # ************** DATA GETTERS ************** #

    def get_trader_snapshot(self, trader_address: Optional[str]) -> list[dict]:
        """
        Get a snapshot of Trader leaves given a particular key.

        Parameters
        ----------
        trader_address : str
            Trader address
        """

        def topic_string(trader_key: TraderKey):
            return f"{'/'.join(filter(None, ['STATE', 'TRADER', trader_key]))}/"

        def encompasses_key(against_key: TraderKey):
            if trader_address is not None:
                return against_key.trader_address == trader_address
            return True

        if all(map(lambda x: x is not None, [trader_address])):
            # If the topic is maximally set, we have a specific leaf
            # we are querying, and can retrieve it from the SMT
            # accordingly

            # Return a snapshot with a single Trader leaf item
            trader_key: TraderKey = TraderKey(trader_address)
            return [{"t": topic_string(trader_key), "c": self.smt.trader(trader_key)}]

        # Return a snapshot containing the Trader leaves obtained
        return [
            {
                "t": topic_string(trader_key),
                "c": trader,
            }
            for trader_key, trader in self.smt.all_traders()
            if encompasses_key(trader_key)
        ]

    def get_strategy_snapshot(
        self, trader_address: Optional[str], strategy_id_hash: Optional[str]
    ) -> list[dict]:
        """
        Get a snapshot of Strategy leaves given a particular key.
        Parameters
        ----------
        trader_address : str
            Trader address
        strategy_id_hash : str
            Strategy ID hash
        """

        def topic_string(strategy_key: StrategyKey):
            return f"{'/'.join(filter(None, ['STATE', 'STRATEGY', strategy_key.trader_address, strategy_key.strategy_id_hash]))}/"

        def encompasses_key(against_key: StrategyKey):
            if strategy_id_hash is not None:
                return (
                    against_key.trader_address == trader_address
                    and against_key.strategy_id_hash == strategy_id_hash
                )
            elif trader_address is not None:
                return against_key.trader_address == trader_address
            return True

        if all(map(lambda x: x is not None, [trader_address, strategy_id_hash])):
            # If the topic is maximally set, we have a specific leaf
            # we are querying, and can retrieve it from the SMT
            # accordingly
            strategy_key: StrategyKey = StrategyKey(trader_address, strategy_id_hash)
            # Return a snapshot with a single Strategy leaf item
            return [
                {"t": topic_string(strategy_key), "c": self.smt.strategy(strategy_key)}
            ]

        # Return a snapshot containing the Trader leaves obtained
        return [
            {
                "t": topic_string(strategy_key),
                "c": strategy,
            }
            for strategy_key, strategy in self.smt.all_strategies()
            if encompasses_key(strategy_key)
        ]

    def get_position_snapshot(
        self,
        symbol: Optional[ProductSymbol],
        trader_address: Optional[str],
        strategy_id_hash: Optional[str],
    ) -> list[dict]:
        """
        Get a snapshot of Position leaves given a particular key.
        Parameters
        ----------
        symbol : ProductSymbol
            Product symbol
        trader_address : str
            Trader address
        strategy_id_hash : str
            Strategy ID hash
        """

        def topic_string(position_key: PositionKey):
            return f"{'/'.join(filter(None, ['STATE', 'POSITION', position_key.symbol, position_key.trader_address, position_key.strategy_id_hash]))}/"

        def encompasses_key(against_key: PositionKey):
            if strategy_id_hash is not None:
                return (
                    against_key.symbol == symbol
                    and against_key.trader_address == trader_address
                    and against_key.strategy_id_hash == strategy_id_hash
                )
            elif trader_address is not None:
                return (
                    against_key.symbol == symbol
                    and against_key.trader_address == trader_address
                )
            elif symbol is not None:
                return against_key.symbol == symbol
            return True

        if all(
            map(lambda x: x is not None, [symbol, trader_address, strategy_id_hash])
        ):
            # If the topic is maximally set, we have a specific leaf
            # we are querying, and can retrieve it from the SMT
            # accordingly
            position_key: PositionKey = PositionKey(
                trader_address, strategy_id_hash, symbol
            )
            # Return a snapshot with a single Position leaf item
            return [
                {"t": topic_string(position_key), "c": self.smt.position(position_key)}
            ]

        # Return a snapshot containing the Position leaves obtained
        return [
            {
                "t": topic_string(position_key),
                "c": position,
            }
            for position_key, position in self.smt.all_positions()
            if encompasses_key(position_key)
        ]

    def get_book_order_snapshot(
        self,
        symbol: Optional[ProductSymbol],
        order_hash: Optional[str],
        trader_address: Optional[str],
        strategy_id_hash: Optional[str],
    ) -> list[dict]:
        """
        Get a snapshot of BookOrder leaves given a particular key.
        Parameters
        ----------
        symbol : ProductSymbol
            Product symbol
        order_hash : str
            Order hash
        trader_address : str
            Trader address
        strategy_id_hash : str
            Strategy ID hash
        """

        def topic_string(
            book_order_key: BookOrderKey, trader_address: str, strategy_id_hash: str
        ):
            return f"{'/'.join(filter(None, ['STATE', 'BOOK_ORDER', book_order_key.symbol, book_order_key.order_hash, trader_address, strategy_id_hash]))}/"

        def encompasses_key(
            against_key: BookOrderKey,
            against_trader_address: str,
            against_strategy_id_hash: str,
        ):
            if strategy_id_hash is not None:
                return (
                    against_key.symbol == symbol
                    and against_trader_address == trader_address
                    and against_strategy_id_hash == strategy_id_hash
                )
            elif trader_address is not None:
                return (
                    against_key.symbol == symbol
                    and against_trader_address == trader_address
                )
            elif symbol is not None:
                return against_key.symbol == symbol
            return True

        if all(
            map(
                lambda x: x is not None,
                [symbol, order_hash, trader_address, strategy_id_hash],
            )
        ):
            # If the topic is maximally set, we have a specific leaf
            # we are querying, and can retrieve it from the SMT
            # accordingly
            book_order_key: BookOrderKey = BookOrderKey(symbol, order_hash)
            # Return a snapshot with a single Position leaf item
            return [
                {
                    "t": topic_string(book_order_key, trader_address, strategy_id_hash),
                    "c": self.smt.book_order(book_order_key),
                }
            ]

        # Return a snapshot containing the BookOrder leaves obtained
        return [
            {
                "t": topic_string(
                    book_order_key,
                    book_order.trader_address,
                    book_order.strategy_id_hash,
                ),
                "c": book_order,
            }
            for book_order_key, book_order in self.smt.all_book_orders()
            if encompasses_key(
                book_order_key,
                book_order.trader_address,
                book_order.strategy_id_hash,
            )
        ]

    def get_insurance_fund_snapshot(self) -> list[dict]:
        """
        Get a snapshot of the organic InsuranceFund leaf.
        """

        # Return a snapshot containing the organic InsuranceFund
        return [
            {
                "t": "STATE/INSURANCE_FUND/",
                "c": self.smt.insurance_fund(InsuranceFundKey()),
            }
        ]

    # ************** WEBSOCKET FUNCTIONALITY ************** #

    async def _handle_tx_log_update_message(self, message: dict) -> None:
        """
        Handle the transaction log message received from the Trader
        API upon subscription. This will be either the Partial (includes
        the state snapshot SMT data as of the most recent
        checkpoint and the transaction log entries from that point
        up until now) or Update messages (streaming messages of
        individual transaction log entries from this point onwards).
        These messages are parsed to get things into the same format
        such that the Auditor can be used as-is by the integration
        tests as well.

        Parameters
        ----------
        message : dict
            Transaction log update message
        """

        if message["t"] == WebsocketEventType.SNAPSHOT:
            # If transaction log message is of type Snapshot, we will
            # need to process the snapshot of state leaves as of the
            # most recent checkpoint and

            # Extract the state snapshot leaves, which is the state
            # snapshot as of the most recent completed checkpoint
            # at the time of subscribing to the transaction log
            parsed_state_snapshot = message["c"]["leaves"]

            # Process the state snapshot
            self.process_state_snapshot(
                int(message["c"]["epochId"]),
                parsed_state_snapshot,
            )

            # Mark that we've received a snapshot
            self._snapshot_received = True

        else:
            # Parse the transaction log entries suitable for the
            # Auditor such that it can be reused as-is by the
            # integration tests
            parsed_tx_log_entry = get_parsed_tx_log_entry(message["c"])

            if self.first_head:
                # If this is the first tx log entry of the head response

                # Check if we're in epoch < 2 and haven't received a snapshot yet
                if not self._snapshot_received:
                    logger.warning(
                        f"Received Head message in epoch {parsed_tx_log_entry['epochId']} without snapshot. Restarting connection to wait for epoch >= 2..."
                    )
                    raise RuntimeError(
                        f"No snapshot available in epoch {parsed_tx_log_entry['epochId']} < 2, restarting..."
                    )

                # Initialize the current local state root hash to the SMT's root
                # hash after having loaded the state snapshot
                self.current_state_root_hash = f"0x{self.smt.root().as_bytes().hex()}"
                self.current_batch_state_root_hash = self.current_state_root_hash

                self.latest_batch_id = parsed_tx_log_entry["batchId"]

                self.first_head = False

            # Process the transaction log entries
            self.process_tx_log_event(
                parsed_tx_log_entry, message["t"] == WebsocketEventType.HEAD
            )

    async def api_auditor_consumer_handler(
        self, websocket: WebSocketClientProtocol, path: str
    ):
        """
        API <> Auditor consumer handler for messages that are received
        by the Auditor from the API.

        Parameters
        ----------
        websocket : WebSocketServerProtocol
            The WS connection instance between API and Auditor
        """

        async def _inner_messages(
            ws: websockets.WebSocketClientProtocol,
        ) -> AsyncIterable[str]:
            try:
                while True:
                    try:
                        msg: str = await asyncio.wait_for(ws.recv(), timeout=30.0)
                        yield msg
                    except asyncio.TimeoutError:
                        try:
                            pong_waiter = await ws.ping()
                            await asyncio.wait_for(pong_waiter, timeout=30.0)
                        except asyncio.TimeoutError:
                            raise
            except asyncio.TimeoutError:
                print("WebSocket ping timed out. Going to reconnect...")
                return
            except websockets.ConnectionClosed:
                return
            finally:
                await ws.close()

        # Loop through messages as they come in on the WebSocket
        async for message in _inner_messages(websocket):
            # JSON-serialize the inbound message
            data = json.loads(message)

            if "t" not in data:
                # Non topical data, such as rate-limiting message
                continue

            topic = data["t"]

            if topic in ["Snapshot", "Head", "Tail"]:
                # If the message is a TxLogUpdate, this is something
                # that should be processed by the Auditor

                # Handle transaction log message
                await self._handle_tx_log_update_message(data)

    async def api_auditor_producer_handler(
        self, websocket: WebSocketClientProtocol, path: str
    ):
        """
        API <> Auditor producer handler for messages that are sent
        from the Auditor to the API.

        Parameters
        ----------
        websocket : WebSocketServerProtocol
            The WS connection instance between API and Auditor
        """

        # Start things off with a subscription to the TxLogUpdate
        # channel on the API to receive a snapshot and streaming
        # updates to the transaction log
        tx_log_update_subscription = WebsocketMessage(
            "SubscribeMarket", {"events": ["TxLogUpdate"]}
        )
        self.api_auditor_queue.put_nowait(tx_log_update_subscription)

        try:
            while True:
                # Receive the oldest message (FIFO) in the queue and
                # send after serialization to the API
                message = await self.api_auditor_queue.get()
                await websocket.send(ComplexOutputEncoder().encode(message))
        except websockets.ConnectionClosed:
            print("Connection has been closed (api_auditor_producer_handler)")

    async def api_auditor_server(self):
        """
        sets up the DerivaDEX API <> Auditor server with consumer and
        producer tasks. The consumer is when the Auditor receives
        messages from the API, and the producer is when the Auditor
        sends messages to the API.
        """

        def _generate_uri_token():
            """
            Generate URI token to connect to the API
            """

            # Construct and return WS connection url with format
            return f"{self.webserver_url.replace('http','ws',1)}/v2/txlog"

        while True:
            try:
                # set up a WS context connection given a specific URI
                async with websockets.connect(
                    _generate_uri_token(),
                    max_size=2**32,
                    ping_timeout=None,
                ) as websocket_client:
                    try:
                        # set up the consumer
                        consumer_task = asyncio.ensure_future(
                            self.api_auditor_consumer_handler(websocket_client, None)
                        )

                        # set up the producer
                        """
                        producer_task = asyncio.ensure_future(
                            self.api_auditor_producer_handler(websocket_client, None)
                        )
                        """

                        # These should essentially run forever unless one of them
                        # is stopped for some reason
                        done, pending = await asyncio.wait(
                            [consumer_task],
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                        for task in pending:
                            task.cancel()
                    finally:
                        logger.info(f"API <> Auditor server outer loop restarting")

                        await asyncio.sleep(30.0)

                        self._reset()
                        continue

            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(
                    f"Unexpected error with WebSocket connection: {e}. Retrying after 30 seconds...",
                )
                await asyncio.sleep(30.0)

                # Reset Auditor state upon reconnection
                self._reset()

    def shutdown_operators(self):
        node_urls = [
            url.strip("/")
            for url in requests.get(f"{self.webserver_url}/v2/status")
            .json()["raftMetrics"]["nodes"]
            .values()
        ]

        for url in node_urls:
            r = requests.get(f"{url}/v2/shutdown")
            logger.info(f"shutting down operator node at {url} succeeded: {r.ok}")

    # ************** ASYNCIO ENTRYPOINT ************** #

    async def main(self):
        """
        Main entry point for the Auditor. It sets up the various
        coroutines to run on the event loop - API <> auditor WS server.
        """

        # Initialize parameters inside event loop
        self._reset()

        await asyncio.gather(self.api_auditor_server())
