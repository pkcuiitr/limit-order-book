"""
Author: Danish Shah (sdanish1998@gmail.com)
Date: 10/4/2023
Last Modified: 10/4/2023

This file contains the OrderBookSnapshot and OrderBookHistory classes
that caaan be used to store the instantaneous state of the order-book
and a series of states respectively.
"""

import bisect
import pandas as pd

class OrderBookSnapshot:
    """Object containing the state of the order-book at a given instance"""

    def __init__(self, time, tick, nbb, nbo, bid_vol, ask_vol):
        self.timestamp = time
        self.tick = tick
        self.nbb = nbb
        self.nbo = nbo
        self.bid_vol = bid_vol
        self.ask_vol = ask_vol

    def __lt__(self, other):
        if isinstance(other, OrderBookSnapshot):
            return self.timestamp < other.timestamp
        if isinstance(other, (int, float)):
            return self.timestamp < other
        return NotImplemented

    def __str__(self):
        bids, asks = {}, {}
        for i, volume in enumerate(self.bid_vol):
            bids[self.nbb - i*self.tick] = volume
        for i, volume in enumerate(self.ask_vol):
            asks[self.nbo + i*self.tick] = volume
        return str({'timestamp': self.timestamp, 'bids': bids, 'asks': asks})

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
