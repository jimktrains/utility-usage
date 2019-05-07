#!/usr/bin/env python3

import amwater
import duqlight
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

def print_results(results):
    for result in results:
        account = result['account']
        usage   = result['usage']
        bills   = result['bills']
        print(f"Account {account}")
        print("Usage:")
        for usage in usage:
            print(usage)
        print("Bills:")
        for bill in bills:
            print(bill)

results = amwater.get_usage(config['amwater'])
print_results(results)


results = duqlight.get_usage(config['duqlight'])
print_results(results)

