"""
Author: Danish Shah (sdanish1998@gmail.com)
Date: 10/7/2023
Last Modified: 10/7/2023

This file contains objects to store and access the
contents of the YAML configuration file.
"""

import yaml

class Config:
    """Object to store configuration settings"""

    def __init__(self, config_file: str):
        # Default values
        self.start_time = 0
        self.end_time = 60000
        self.open_window = 60
        self.close_window = 60
        self.timestep_ms = 100
        self.tick_size = 0.01
        self.start_bid = 100.00
        self.start_ask = 100.01
        self.max_depth = 5
        self.market_order_rate = 2.0
        self.limit_order_rate = 5.0
        self.mean_deviation = 2.00
        self.market_volume_rate = 10
        self.limit_volume_rate = 10
        self.jump_rate = 1000.0
        self.cancel_order_rate = 1.0
        self.cancel_volume_rate = 3
        self.price_method = 'mid'
        self.allow_market_orders = True
        self.allow_cancel_orders = True
        self.allow_mid_orders = False
        self.output_file = 'simulation_result.csv'

        # Load values from the yaml file
        with open(config_file, 'r', encoding='utf8') as file:
            config_data = yaml.safe_load(file)
            for key, value in config_data.items():
                # Only update attributes that have default values
                if hasattr(self, key):
                    setattr(self, key, value)
