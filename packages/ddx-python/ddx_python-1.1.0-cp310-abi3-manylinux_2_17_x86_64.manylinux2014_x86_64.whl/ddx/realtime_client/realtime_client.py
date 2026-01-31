import os
import asyncio
import json
import websockets
from websockets import WebSocketClientProtocol
import logging
from .models import (
    TradeSide,
    FeedWithParams,
    MarkPriceParams,
    OrderBookL2Filter,
    OrderBookL2Params,
    OrderBookL3Order,
    SubscribePayload,
    UnsubscribePayload,
    AcknowledgePayload,
    OrderBookL2Payload,
    OrderBookL3Payload,
    MarkPricePayload,
    OrderUpdatePayload,
    StrategyUpdatePayload,
    TraderUpdatePayload,
    OrderBookL2Contents,
    OrderBookL3Contents,
    MarkPriceContents,
    Feed,
    MessageType,
    Action,
    FeedPayload,
    SubscriptionPayload,
)
from typing import Awaitable, Callable, Optional, AsyncGenerator

from ddx._rust.decimal import Decimal

from .config import DEFAULT_RETRY_DELAY, MAX_RETRY_DELAY


class RealtimeClient:
    """
    The DerivaDEX Realtime API client.

    This client connects to the DerivaDEX realtime WebSockets API to subscribe to various
    data feeds such as order book snapshots (L2 and L3), mark prices, as well as
    updates for orders, strategies, and traders.
    """

    def __init__(self, ws_url: str):
        self._ws_url = ws_url

        self._connection: Optional[WebSocketClientProtocol] = None
        self._pending = {}
        self._update_queue = asyncio.Queue()
        self._listener_task = None
        self._nonce = 0
        # Active subscriptions: maps feed kind -> FeedWithParams.
        # Keys give O(1) membership checks, values keep the latest params.
        self._subscriptions: dict[Feed, FeedWithParams] = {}
        # Internal state for special feeds
        # L2 order book: symbol -> side (TradeSide) -> price -> amount (str)
        self._order_book_l2_state: dict[str, dict[TradeSide, dict[str, str]]] = {}
        self._order_book_l3_state: dict[str, OrderBookL3Order] = {}
        self._mark_price_state: dict[str, str] = {}
        self._funding_rate_state: dict[str, str] = {}
        # Dictionary mapping each feed to its registered callback.
        # If no callback is provided for a given feed, it will default to no operation.
        self._callbacks: dict[
            Feed,
            Callable[[FeedPayload], None] | Callable[[FeedPayload], Awaitable[None]],
        ] = {}

    def _get_next_nonce(self) -> str:
        nonce = str(self._nonce)
        self._nonce += 1
        return nonce

    def _dispatch_message(self, msg: dict):
        nonce = msg.get("nonce")
        if "result" in msg and nonce and nonce in self._pending:
            future = self._pending.pop(nonce)
            try:
                ack = AcknowledgePayload.model_validate(msg)
            except Exception as exc:
                logging.exception(f"Failed to decode acknowledgement message; nonce={nonce} msg={msg}")
                future.set_exception(exc)
                return
            future.set_result(ack)
            logging.debug(f"Dispatched acknowledgement message with nonce: {nonce}")
            return
        feed = msg.get("feed")
        if feed is not None:
            try:
                feed_enum = Feed(feed)
            except Exception:
                logging.error(f"Unknown feed value in message: {feed} msg={msg}")
                return

            try:
                if feed_enum == Feed.ORDER_BOOK_L2:
                    payload = OrderBookL2Payload.model_validate(msg)
                    self._update_order_book_l2(payload.contents)
                elif feed_enum == Feed.ORDER_BOOK_L3:
                    payload = OrderBookL3Payload.model_validate(msg)
                    self._update_order_book_l3(payload.contents)
                elif feed_enum == Feed.MARK_PRICE:
                    payload = MarkPricePayload.model_validate(msg)
                    self._update_mark_price(payload.contents)
                elif feed_enum == Feed.ORDER_UPDATE:
                    payload = OrderUpdatePayload.model_validate(msg)
                elif feed_enum == Feed.STRATEGY_UPDATE:
                    payload = StrategyUpdatePayload.model_validate(msg)
                elif feed_enum == Feed.TRADER_UPDATE:
                    payload = TraderUpdatePayload.model_validate(msg)
                else:
                    logging.error(f"Unhandled feed enum in message: {feed_enum}")
                    return
            except Exception as exc:
                logging.exception(f"Failed to decode/handle message for feed {feed_enum}; msg={msg}")
                return

            if feed_enum in self._callbacks:
                callback = self._callbacks[feed_enum]
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(payload))
                    else:
                        callback(payload)
                except Exception as exc:
                    logging.exception(f"Error in callback for feed {feed_enum}: {exc}")
            else:
                self._update_queue.put_nowait(payload)

    async def _listen(self):
        """
        Internal method to continuously listen for incoming messages,
        dispatching responses (with nonce) to pending requests,
        and placing all other messages into the update queue.
        """
        assert (
            self._connection is not None
        ), "Connection must be established before listening."
        while True:
            logging.debug("Update queue size: %d", self._update_queue.qsize())
            try:
                msg_raw = await self._connection.recv()
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                await self.disconnect()
                await self.connect()
                break
            try:
                msg = json.loads(msg_raw)
            except Exception as e:
                logging.exception(f"Failed to parse incoming WS message; raw={msg_raw}")
                continue
            try:
                self._dispatch_message(msg)
            except Exception as e:
                logging.exception(f"Unhandled error dispatching WS message; raw={msg_raw} parsed={msg}")
                continue

    async def receive_message(self, feed_name: Feed) -> FeedPayload:
        """
        Wait for an update message with the specified feed.
        """
        while True:
            payload = await self._update_queue.get()
            if payload.feed == feed_name:
                logging.debug(f"Retrieved message for feed: {feed_name} from queue.")
                return payload

    async def connect(self) -> None:
        """
        Establish a WebSocket connection with reconnection logic.
        """
        delay = DEFAULT_RETRY_DELAY
        while True:
            try:
                self._connection = await websockets.connect(self._ws_url)
                break
            except Exception as e:
                logging.error(f"Connection failed: {e}. Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay = min(delay * 2, MAX_RETRY_DELAY)
        self._listener_task = asyncio.create_task(self._listen())
        # Restore any subscriptions that were active before a disconnect
        if self._subscriptions:
            await self._resubscribe()

    async def disconnect(self) -> None:
        """
        Close the WebSocket connection, cancel the listener task,
        and cancel any pending request futures.
        """
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                logging.info("Listener task cancelled successfully.")
        # Cancel any pending futures
        for nonce, future in self._pending.items():
            if not future.done():
                future.cancel()
                logging.info(f"Cancelled pending future for nonce: {nonce}")
        self._pending.clear()
        if self._connection:
            await self._connection.close()
            logging.info("Connection closed.")

    async def _send(self, message) -> None:
        """
        Send a message over the WebSocket connection.
        If the message is not a string, it is assumed to be a dict and will be JSON-serialized.
        Raises RuntimeError if no active connection exists.
        """
        if not self._connection:
            raise RuntimeError("No active connection to send message.")
        if not isinstance(message, str):
            message = json.dumps(message)
        logging.info(f"Sending message: {message}")
        await self._connection.send(message)

    async def _send_request(self, payload: SubscriptionPayload) -> AcknowledgePayload:
        """
        Send a request payload and await an acknowledgement.

        This method registers a future keyed by the payload's nonce, then sends the JSON-serialized
        payload over the WebSocket connection. It waits (up to 10 seconds) for an acknowledgement.
        In case of a timeout, the pending future is cancelled and a TimeoutError is raised.

        Nonce generation for each request is handled automatically via _get_next_nonce.
        """
        future = asyncio.get_running_loop().create_future()
        self._pending[payload.nonce] = future
        try:
            await self._send(payload.model_dump_json())
            logging.info(f"Request sent with nonce: {payload.nonce}")
        except Exception as exc:
            logging.error(f"Failed to send payload with nonce {payload.nonce}: {exc}")
            future.cancel()
            raise
        try:
            ack = await asyncio.wait_for(future, timeout=10)
        except asyncio.TimeoutError:
            logging.error(
                f"Timeout waiting for acknowledgement for nonce: {payload.nonce}"
            )
            self._pending.pop(payload.nonce, None)
            raise
        logging.debug(f"Received acknowledgement for nonce: {payload.nonce}")
        return ack

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    async def subscribe(
        self,
        payload: SubscribePayload,
        callbacks: Optional[
            dict[
                Feed,
                Callable[[FeedPayload], None]
                | Callable[[FeedPayload], Awaitable[None]],
            ]
        ] = None,
    ) -> AcknowledgePayload:
        """
        Send a subscription request and wait for an acknowledgement.

        Optionally, register a dictionary mapping feeds to callback functions. Callbacks provided
        here are merged with any existing callback registrations. Callback functions can be either
        synchronous or asynchronous; if asynchronous (i.e. a coroutine function), they will be scheduled
        using asyncio.create_task to avoid blocking message dispatch.

        The acknowledgement received will confirm the subscription, with the nonce matching the request.
        """
        ack = await self._send_request(payload)
        if callbacks is not None:
            self._callbacks.update(callbacks)
        return ack

    async def subscribe_feeds(
        self,
        feeds: list[
            FeedWithParams
            | tuple[
                FeedWithParams,
                Callable[[FeedPayload], None]
                | Callable[[FeedPayload], Awaitable[None]],
            ],
        ],
    ) -> AcknowledgePayload:
        payload_feeds: list[FeedWithParams] = []
        callbacks: dict[
            Feed,
            Callable[[FeedPayload], None] | Callable[[FeedPayload], Awaitable[None]],
        ] = {}
        for item in feeds:
            if isinstance(item, tuple):
                feed_with_params, callback = item
                payload_feeds.append(feed_with_params)
                callbacks[feed_with_params.feed] = callback
            else:
                payload_feeds.append(item)
        nonce = self._get_next_nonce()
        payload = SubscribePayload(
            action=Action.SUBSCRIBE,
            nonce=nonce,
            feeds=payload_feeds,
        )
        ack = await self.subscribe(payload, callbacks)
        if ack.result.error is not None:
            raise RuntimeError(f"Subscription failed with error: {ack.result.error}")
        # Persist/overwrite successful subscriptions
        for new_fw in payload_feeds:
            self._subscriptions[new_fw.feed] = new_fw
        return ack

    async def unsubscribe(self, payload: UnsubscribePayload) -> AcknowledgePayload:
        """
        Send an unsubscription request and wait for an acknowledgement.
        """
        return await self._send_request(payload)

    async def unsubscribe_feeds(
        self,
        feeds: list[Feed],
    ):
        nonce = self._get_next_nonce()
        payload = UnsubscribePayload(
            action=Action.UNSUBSCRIBE,
            nonce=nonce,
            feeds=feeds,
        )
        ack = await self.unsubscribe(payload)
        if ack.result.error is not None:
            raise RuntimeError(f"Unsubscription failed with error: {ack.result.error}")
        for feed in feeds:
            self._subscriptions.pop(feed, None)
            self._callbacks.pop(feed, None)

    async def receive_order_book_l2(self) -> AsyncGenerator[OrderBookL2Payload, None]:
        """
        Listen continuously for Order Book L2 updates.
        """
        if Feed.ORDER_BOOK_L2 not in self.subscribed:
            raise RuntimeError(
                "Order Book L2 feed is not subscribed. Please subscribe first."
            )
        while True:
            payload = await self.receive_message(Feed.ORDER_BOOK_L2)
            assert isinstance(payload, OrderBookL2Payload)
            yield payload

    async def receive_order_book_l3(self) -> AsyncGenerator[OrderBookL3Payload, None]:
        """
        Listen continuously for Order Book L3 updates.
        """
        if Feed.ORDER_BOOK_L3 not in self.subscribed:
            raise RuntimeError(
                "Order Book L3 feed is not subscribed. Please subscribe first."
            )
        while True:
            payload = await self.receive_message(Feed.ORDER_BOOK_L3)
            assert isinstance(payload, OrderBookL3Payload)
            yield payload

    async def receive_mark_price(self) -> AsyncGenerator[MarkPricePayload, None]:
        """
        Listen continuously for Mark Price updates.
        """
        if Feed.MARK_PRICE not in self.subscribed:
            raise RuntimeError(
                "Mark Price feed is not subscribed. Please subscribe first."
            )
        while True:
            payload = await self.receive_message(Feed.MARK_PRICE)
            assert isinstance(payload, MarkPricePayload)
            yield payload

    async def receive_order_update(self) -> AsyncGenerator[OrderUpdatePayload, None]:
        """
        Listen continuously for Order Update messages.
        """
        if Feed.ORDER_UPDATE not in self.subscribed:
            raise RuntimeError(
                "Order Update feed is not subscribed. Please subscribe first."
            )
        while True:
            payload = await self.receive_message(Feed.ORDER_UPDATE)
            assert isinstance(payload, OrderUpdatePayload)
            yield payload

    async def receive_strategy_update(
        self,
    ) -> AsyncGenerator[StrategyUpdatePayload, None]:
        """
        Listen continuously for Strategy Update messages.
        """
        if Feed.STRATEGY_UPDATE not in self.subscribed:
            raise RuntimeError(
                "Strategy Update feed is not subscribed. Please subscribe first."
            )
        while True:
            payload = await self.receive_message(Feed.STRATEGY_UPDATE)
            assert isinstance(payload, StrategyUpdatePayload)
            yield payload

    async def receive_trader_update(self) -> AsyncGenerator[TraderUpdatePayload, None]:
        """
        Listen continuously for Trader Update messages.
        """
        if Feed.TRADER_UPDATE not in self.subscribed:
            raise RuntimeError(
                "Trader Update feed is not subscribed. Please subscribe first."
            )
        while True:
            payload = await self.receive_message(Feed.TRADER_UPDATE)
            assert isinstance(payload, TraderUpdatePayload)
            yield payload

    @property
    def subscribed(self) -> set[Feed]:
        """
        Current set of feed kinds we are subscribed to.
        """
        return set(self._subscriptions.keys())

    @property
    def order_book_l2(self) -> dict[str, dict[TradeSide, dict[str, str]]]:
        """
        Returns a deep copy of the current Order Book L2 state:
            { symbol: { side(TradeSide): { price: amount_str } } }
        """
        return {
            s: {sd: lvls.copy() for sd, lvls in sides.items()}
            for s, sides in self._order_book_l2_state.items()
        }

    def aggregated_order(
        self, symbol: str
    ) -> Optional[dict[TradeSide, dict[str, str]]]:
        """
        Return a snapshot for `symbol` (if available) in the same
        nested-dict format used by `order_book_l2`:

            { side(TradeSide): { price: amount_str } }
        """
        return self._order_book_l2_state.get(symbol)

    @property
    def order_book_l3(self) -> dict[str, OrderBookL3Order]:
        """
        Returns a copy of the current Order Book L3 state.
        """
        return self._order_book_l3_state.copy()

    def order(self, order_hash: str) -> Optional[OrderBookL3Order]:
        """
        Returns the order for a specific order hash.
        """
        return self._order_book_l3_state.get(order_hash)

    @property
    def mark_prices(self) -> dict[str, str]:
        """
        Returns a copy of the current Mark Price state.
        """
        return self._mark_price_state.copy()

    def mark_price(self, symbol: str) -> Optional[str]:
        """
        Returns the mark price for a specific symbol.
        """
        return self._mark_price_state.get(symbol)

    @property
    def funding_rates(self) -> dict[str, str]:
        """
        Returns a copy of the current Funding Rate state.
        """
        return self._funding_rate_state.copy()

    def funding_rate(self, symbol: str) -> Optional[str]:
        """
        Returns the funding rate for a specific symbol.
        """
        return self._funding_rate_state.get(symbol)

    # --- Internal state update methods for special feeds ---
    def _update_order_book_l2(self, contents: OrderBookL2Contents):
        """
        Maintain an in-memory L2 book:
            { symbol: { side(TradeSide): { price: amount_str } } }

        A PARTIAL message replaces the entire book for the given symbol,
        while an UPDATE message applies deltas.  When the incoming
        amount is the string "0" the corresponding price level is
        removed.  Empty side / symbol maps are pruned.
        """
        update_type = contents.message_type
        data = contents.data

        if update_type == MessageType.PARTIAL:
            # Build fresh maps for only the symbols present in this snapshot
            snapshot: dict[str, dict[TradeSide, dict[str, str]]] = {}
            for lvl in data:
                symbol, side = lvl.symbol, lvl.side
                snapshot.setdefault(symbol, {}).setdefault(side, {})[
                    lvl.price
                ] = lvl.amount
            # Replace the symbols present in the snapshot; keep others intact
            for symbol, book in snapshot.items():
                self._order_book_l2_state[symbol] = book
        elif update_type == MessageType.UPDATE:
            for delta in data:
                sym, side, price, amt = (
                    delta.symbol,
                    delta.side,
                    delta.price,
                    delta.amount,
                )
                if Decimal(amt) == Decimal("0"):
                    # remove level if it exists
                    side_levels = self._order_book_l2_state.get(sym, {}).get(side)
                    if side_levels is not None:
                        side_levels.pop(price, None)
                        # prune empty dicts
                        if not side_levels:
                            self._order_book_l2_state[sym].pop(side, None)
                            if not self._order_book_l2_state[sym]:
                                self._order_book_l2_state.pop(sym, None)
                else:
                    self._order_book_l2_state.setdefault(sym, {}).setdefault(side, {})[
                        price
                    ] = amt

    def _update_order_book_l3(self, contents: OrderBookL3Contents):
        """
        Update the internal order book L3 state with a PARTIAL snapshot or delta UPDATE.
        Here we key by the unique orderHash.
        """
        update_type = contents.message_type
        data = contents.data
        if update_type == MessageType.PARTIAL:
            state = {}
            for order in data:
                state[order.order_hash] = order
            self._order_book_l3_state = state
        elif update_type == MessageType.UPDATE:
            for delta in data:
                key = delta.order_hash
                if Decimal(delta.amount) == Decimal("0"):
                    self._order_book_l3_state.pop(key, None)
                else:
                    self._order_book_l3_state[key] = delta

    def _update_mark_price(self, contents: MarkPriceContents):
        """
        Update the mark price state which is a dict mapping symbols to mark prices.
        A PARTIAL sets the full state and an UPDATE modifies only the entries provided.
        """
        update_type = contents.message_type
        data = contents.data
        if update_type == MessageType.PARTIAL:
            mark_price_state = {}
            funding_rate_state = {}
            for entry in data:
                mark_price_state[entry.symbol] = entry.price
                funding_rate_state[entry.symbol] = entry.funding_rate
            self._mark_price_state = mark_price_state
            self._funding_rate_state = funding_rate_state
        elif update_type == MessageType.UPDATE:
            for entry in data:
                self._mark_price_state[entry.symbol] = entry.price
                self._funding_rate_state[entry.symbol] = entry.funding_rate

    async def _resubscribe(self) -> None:
        """
        Re-establish every subscription that existed before the last disconnect.
        """
        if not self._subscriptions:
            return

        feeds_spec = []
        for fw in self._subscriptions.values():
            cb = self._callbacks.get(fw.feed)
            feeds_spec.append((fw, cb) if cb is not None else fw)

        try:
            await self.subscribe_feeds(feeds_spec)
            logging.info("Resubscribed to previous feeds.")
        except Exception as exc:
            logging.error(f"Resubscription failed: {exc}")


if __name__ == "__main__":

    async def main():
        client = RealtimeClient(
            os.environ.get(
                "REALTIME_API_WS_URL", "wss://exchange.derivadex.com/realtime-api"
            )
        )
        await client.connect()

        def handle_mark_price(payload):
            print(f"Mark Price Update: {payload.contents}")

        ack = await client.subscribe_feeds(
            [
                FeedWithParams(
                    feed=Feed.ORDER_BOOK_L2,
                    params=OrderBookL2Params(
                        order_book_l2_filters=[
                            OrderBookL2Filter(symbol="ETHP", aggregation=1)
                        ]
                    ),
                ),
                (
                    FeedWithParams(
                        feed=Feed.MARK_PRICE,
                        params=MarkPriceParams(symbols=["ETHP", "BTCP"]),
                    ),
                    handle_mark_price,
                ),
            ]
        )
        print("Subscription Acknowledgement:", ack)

        print("Waiting for Order Book L2 snapshot...")
        update = await anext(client.receive_order_book_l2())
        print("Received Order Book L2 snapshot:", update)

        print("Waiting for Mark Price update...")
        mark_price_update = await anext(client.receive_mark_price())
        print("Received Mark Price update:", mark_price_update)

        await client.disconnect()

    asyncio.run(main())
