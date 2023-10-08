"""
Author: Danish Shah (sdanish1998@gmail.com)
Date: 10/6/2023
Last Modified: 10/7/2023

This file contains the objects that represent the market
participants. They are used to place orders and trades
in the order book.
"""

import math
import numpy as np
from numpy import random

from configuration import Config
from lob import Side, OrderType, Order, OrderBookSnapshot

class Market:
    """Object representing the market as a whole"""

    def __init__(self, config):
        self.market_order_rate = config.market_order_rate
        self.limit_order_rate = config.limit_order_rate
        self.cancel_order_rate = config.cancel_order_rate
        self.market_volume_rate = config.market_volume_rate
        self.limit_volume_rate = config.limit_volume_rate
        self.cancel_volume_rate = config.cancel_volume_rate
        self.timestep_ms = config.timestep_ms
        self.state = 0.0
        self.price_drift = 0.0
        self.mean_reversion = 0.01
        self.mean_deviation = 0.2

    @classmethod
    def from_config(cls, config: Config):
        """Returns a new Market based on configuration settings"""
        return cls(config)

    @staticmethod
    def bound(x, min_val=0, max_val=1):
        """Returns a bounded value using sigmoid function"""
        return min_val + (max_val-min_val) / (1 + math.exp(-x))

    @staticmethod
    def exp_dist(rate, min_val=None, max_val=None):
        """Returns an exponentially distributed random integer with given bounds"""
        val = int(random.exponential(scale=rate))
        return max(min_val or float('-inf'), min(val, max_val or float('inf')))

    def get_next_order(self, snapshot: OrderBookSnapshot) -> Order:
        """Generates the next order to the order-book"""
        # Order side based on current state of the market
        self.state += (self.mean_reversion * (self.price_drift - self.state) +
               random.normal(scale=self.mean_deviation))
        buy_prob = Market.bound(self.state)
        side = random.choice([Side.BUY, Side.SELL], p=[buy_prob, 1-buy_prob])

        depth = snapshot.book_depth
        # Compute probabilities for limit orders at each level
        ord_limit = [OrderType.LIMIT_ORDER] * (depth + snapshot.spread - 1)
        prob_limit = [
            self.limit_order_rate / i
            for i in range(1, depth + snapshot.spread)
        ]
        lvl_limit = np.arange(start=1, stop=depth+snapshot.spread).tolist()
        # Compute probabilities for cancel orders at each level
        ord_cancel = [OrderType.CANCEL_ORDER] * depth
        prob_cancel = [
            self.cancel_order_rate * (depth - i - 1) / depth
            for i in range(depth)
        ]
        lvl_cancel = np.arange(start=0, stop=depth).tolist()

        # Create OrderType and probability list for all levels
        ord_type, prob, lvl = [OrderType.MARKET_ORDER], [self.market_order_rate], [0]
        ord_type.extend(ord_limit + ord_cancel)
        prob.extend(prob_limit + prob_cancel)
        lvl.extend(lvl_limit + lvl_cancel)

        # Normalize the probabilities
        total_rate = np.sum(prob)
        prob = prob / total_rate

        # Order Type based on relative probabilities
        idx = random.choice(range(len(prob)), p=prob)
        order_type, level = ord_type[idx], lvl[idx]

                # Order quantity based on order type
        rate_mapping = {
            OrderType.CANCEL_ORDER: self.cancel_volume_rate,
            OrderType.MARKET_ORDER: self.market_volume_rate,
            OrderType.LIMIT_ORDER: self.limit_volume_rate
        }
        qty = Market.exp_dist(rate_mapping.get(order_type), min_val=0)

        # Order timestamp
        time_till_next = int(-self.timestep_ms * np.log(random.uniform(1e-3, 1)) / total_rate)
        time = snapshot.timestamp + time_till_next

        return Order(time, order_type, side, level, qty)
