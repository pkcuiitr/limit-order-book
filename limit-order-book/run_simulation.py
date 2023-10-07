"""
Author: Danish Shah (sdanish1998@gmail.com)
Date: 10/5/2023
Last Modified: 10/7/2023

This script file is called to run and save the results of an 
order-book simulation. The input parameters are specified in 
the configuration file.
"""

import pandas as pd

from configuration import Config
from lob import Order, OrderBookSnapshot, OrderBookHistory
from market import Market

def run_orderbook_simulation(config: Config):
    """Runs and saves the result of order-book simulation according to the config"""
    orderbook = OrderBookHistory.from_config(config)
    mkt = Market.from_config(config)
    while orderbook.end_time < config.end_time:
        snapshot = orderbook.get_latest_snapshot()
        new_order = mkt.get_next_order(snapshot)
        new_snapshot = snapshot.update(new_order)
        orderbook.add_snapshot(new_snapshot)
    orderbook.get_nbbo_history().to_csv(config.output_file)
    return orderbook

if __name__ == "__main__":
    config = Config('config.yaml')
    run_orderbook_simulation(config)
