#!/usr/bin/env python3

import amwater
import duqlight
from configparser import ConfigParser
import os
import sqlite3
import cache
import storage

config = ConfigParser()
config.read('config.ini')

download_path = config['storage']['download_path']

cache.init(download_path)
storage.init(download_path)

def print_results(results):
    for result in results:
        account = result['account']
        usage   = result['usage']
        bills   = result['bills']
        print(f"Account {account}")
        account_dbid = storage.insert_account(account)
        if account_dbid is None or account_dbid == 0:
            print("!!!!!!!!!!!!!!!")
            break
        print(f"Account DBID: {account_dbid}")
        print("Usage:")
        for usage in usage:
            storage.insert_usage(account_dbid, usage)
            print(usage)
        print("Bills:")
        for bill in bills:
            storage.insert_bill(account_dbid, bill)
            print(bill)

results = amwater.get_usage(config['amwater'], download_path)
print_results(results)


results = duqlight.get_usage(config['duqlight'], download_path)
print_results(results)

