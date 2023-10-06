"""
Author: Danish Shah (sdanish1998@gmail.com)
Date: 10/5/2023
Last Modified: 10/5/2023

This script file is called to run and save the results of an 
order-book simulation. The input parameters are specified in 
the config file.
"""

import yaml

def run_orderbook_simulation(conf):
    """Runs and saves the result of order-book simulation according to the config"""
    print(conf)

if __name__ == "__main__":
    with open('config.yaml', encoding='UTF-8') as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)
    run_orderbook_simulation(conf)
