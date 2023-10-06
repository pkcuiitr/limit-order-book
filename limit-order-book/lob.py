"""
Author: Danish Shah (sdanish1998@gmail.com)
Date: 10/4/2023
Last Modified: 10/6/2023

This file contains the OrderBookSnapshot and OrderBookHistory classes
that can be used to store the instantaneous state of the order-book
and a series of states respectively.
"""

from enum import Enum
from copy import deepcopy
import bisect
import pandas as pd

class OrderType(Enum):
    """Type of order"""
    MARKET_ORDER = 1
    LIMIT_ORDER = 2
    CANCEL_ORDER = 3
    MIDPOINT_ORDER = 4

class Side(Enum):
    """Side of order"""
    BUY = 1
    SELL = 2

class Trade:
    """Object representing an executed trade"""

    def __init__(self, timestamp, price, qty, order_type, exec_id=None):
        self.timestamp = timestamp
        self.price = price
        self.qty = qty
        self.order_type = order_type
        self.exec_id = exec_id if exec_id else 'E' + str(id(self))

    def __str__(self) -> str:
        txt = "{exec_id}: {order_type} for {qty} shares at ${price}"
        return txt.format(self.exec_id, self.order_type.name, self.qty, self.price)

class Order:
    """Object representing an order to the exchange"""

    def __init__(self, timestamp, order_type, side, level, qty, order_id=None):
        self.timestamp = timestamp
        self.order_type = order_type
        self.side = side
        self.level = level
        self.qty = qty
        self.partial_fill = True
        self.order_id = order_id if order_id else 'O' + str(id(self))

    def __str__(self) -> str:
        txt = "{order_id}: {order_type} for {qty} shares at level {level}"
        return txt.format(self.order_id, self.order_type.name, self.qty, self.level)

class OrderBookSnapshot:
    """Object containing the state of the order-book at a given instance"""

    def __init__(self, time, tick, nbb, nbo, bid_vol, ask_vol, book_depth):
        self.timestamp = time
        self.tick = tick
        self.nbb = nbb
        self.nbo = nbo
        self.spread = int((nbo - nbb) / tick)
        self.bid_vol = bid_vol
        self.ask_vol = ask_vol
        self.book_depth = book_depth
        self.trades = []

    def __lt__(self, other):
        if isinstance(other, OrderBookSnapshot):
            return self.timestamp < other.timestamp
        if isinstance(other, (int, float)):
            return self.timestamp < other
        return NotImplemented

    def __str__(self) -> str:
        bids, asks = {}, {}
        for i, volume in enumerate(self.bid_vol):
            bids[self.nbb - i*self.tick] = volume
        for i, volume in enumerate(self.ask_vol):
            asks[self.nbo + i*self.tick] = volume
        return str({'timestamp': self.timestamp, 'bids': bids, 'asks': asks})

    def update_trade(self, price, qty, order_type):
        """Adds an execution to the order-book snapshot"""
        self.trades.append(Trade(self.timestamp, price, qty, order_type))

    def process_cancel_order(self, new_order: Order):
        """Updates an order-book after a market order"""

        # Get the parameters based on side of the order
        book_map = {
            'BUY': ('bid_vol', 'nbb', -self.tick),
            'SELL': ('ask_vol', 'nbo', self.tick)
        }
        attr_vol, attr_nbbo, tick_adj = book_map[new_order.side.name]
        book_vol = getattr(self, attr_vol)

        # Reduce the volume at the given level
        book_vol[new_order.level] -= min(new_order.qty, book_vol[new_order.level])
        # Adjust NBBO if required
        if new_order.level == 0 and book_vol[0] == 0:
            book_vol.pop(0)
            setattr(self, attr_nbbo, getattr(self, attr_nbbo) + tick_adj)
        setattr(self, attr_vol, book_vol)

    def process_market_order(self, new_order: Order):
        """Updates an order-book after a market order"""

        # Get the parameters based on side of the order
        book_map = {
            'BUY':  ('ask_vol', 'nbo', self.tick),
            'SELL': ('bid_vol', 'nbb', -self.tick)
        }
        attr_vol, attr_nbbo, tick_adj = book_map[new_order.side.name]
        book_vol, nbbo = getattr(self, attr_vol), getattr(self, attr_nbbo)
        order_vol = new_order.qty

        # Sweep the order-book till all the volume/book is executed
        price = nbbo
        while order_vol > 0 and book_vol:
            trade_volume = min(order_vol, book_vol[0])
            self.update_trade(price, trade_volume, OrderType.MARKET_ORDER)
            order_vol -= trade_volume
            book_vol[0] -= trade_volume
            if book_vol[0] == 0:
                book_vol.pop(0)
                price += tick_adj

        # Update the order snapshot with new values
        setattr(self, attr_vol, book_vol)
        setattr(self, attr_nbbo, price)

    def process_limit_order(self, new_order: Order):
        """Updates an order-book after a limit order"""

        # Get the parameters based on side of the order
        book_map = {
            'BUY':  ('bid_vol', 'nbb', self.tick),
            'SELL': ('ask_vol', 'nbbo', -self.tick)
        }
        attr_vol, attr_nbbo, tick_adj = book_map[new_order.side.name]
        book_vol, nbbo = getattr(self, attr_vol), getattr(self, attr_nbbo)
        order_vol = new_order.qty

        # Add limit order based on the level
        if new_order.level >= self.spread:
            # order level doesn't change current nbbo
            book_vol[new_order.level - self.spread] += order_vol
            if new_order.level == self.spread and book_vol[0] == 0:
                book_vol.pop(0)
                nbbo -= tick_adj
        else:
            # order level changes current nbbo
            book_vol = [0] * (self.spread - new_order.level) + book_vol
            book_vol[0] = order_vol
            nbbo += (self.spread - new_order.level) * tick_adj

        # Update the order snapshot with new values
        setattr(self, attr_vol, book_vol)
        setattr(self, attr_nbbo, nbbo)

    def update(self, new_order):
        """Returns a new snapshot taking into account new orders and executions"""
        new_snapshot = deepcopy(self)
        new_snapshot.timestamp = new_order.timestamp

        # Update the order-book levels based on order type
        match new_order.order_type:
            case OrderType.CANCEL_ORDER:
                self.process_cancel_order(new_order)
            case OrderType.MARKET_ORDER:
                self.process_market_order(new_order)
            case OrderType.LIMIT_ORDER:
                self.process_limit_order(new_order)

        # Add zero volume levels to maintain max depth
        self.bid_vol += [0] * (self.book_depth - len(self.bid_vol))
        self.ask_vol += [0] * (self.book_depth - len(self.ask_vol))
        return new_snapshot

class OrderBookHistory:
    """Object containing the history of order-book states over time"""

    def __init__(self, timestep, start_time, tick, nbb, nbo, book_depth):
        self.timestep = timestep
        self.start_time = start_time
        self.end_time = start_time
        self.tick = tick
        self.current_nbb = nbb
        self.current_nbo = nbo
        self.book_depth = book_depth
        self.snapshots = []

    def add_snapshot(self, snapshot: OrderBookSnapshot):
        """Updates order-book history with the given snapshot"""
        # Check if the snapshot is new
        if self.end_time <= snapshot.timestamp:
            self.end_time = snapshot.timestamp
            self.snapshots.append(snapshot)
            self.current_nbb = snapshot.nbb
            self.current_nbo = snapshot.nbo
        else:
            # Find the index to insert `snapshot` so that the history remains sorted
            index = bisect.bisect_left(self.snapshots, snapshot)
            self.snapshots.insert(index, snapshot)

    def get_latest_snapshot(self) -> OrderBookSnapshot:
        """Returns the latest snapshot"""
        return self.snapshots[-1]

    def get_snapshot(self, timestamp):
        """Returns the snapshot at or just before the input timestamp"""
        return bisect.bisect_left(self.snapshots, timestamp) - 1

    def get_nbbo_history(self):
        """Returns a dataframe of order-book history values"""
        return pd.DataFrame([{
                'Timestamp': snapshot.timestamp, 
                'BidPrice': snapshot.nbb,
                'BidVolume': snapshot.bid_vol[0],
                'AskPrice': snapshot.nbo,
                'AskVolume': snapshot.ask_vol[0]
            } for snapshot in self.snapshots])
