#!/usr/bin/env python3

from bs4 import BeautifulSoup
from cache import fetch_cached
from datetime import datetime
from datetime import timedelta
from models.account import Account
from models.address import Address
from models.bill import Bill
from models.reading import Reading
import glob
import json
import re
import requests
import os

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0',
}

def parse_iso_date(date):
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")

def extract_vue_table(bs):
    data = None
    for script in bs.select('script'):
        if 'VueTable' in script.text:
            g = re.search('.*(\[.*\]);.*', script.text).groups()
            if len(g) == 1:
                data = json.loads(g[0])
                break
    return data

def extract_number(value):
    g = re.search("(\d+)", value).groups()
    date = None,
    if len(g) == 1:
        return g[0]

def select_single(base, selector):
    cells = base.select(selector)
    for cell in cells:
        return cell.text

def all_acounts(session):
    url = "https://myaccount.columbiagaspa.com/dashboard"
    text = fetch_cached(session, "get", url, headers=headers)
    bs = BeautifulSoup(text, "lxml")

    accounts = []
    for row in bs.select('#portal-sidebar'):
        account_number = extract_number(select_single(row, '.portal__account span:nth-of-type(3)'))

        street_1 = select_single(row, '.portal__account span:nth-of-type(5)')
        city_state_zip = select_single(row, '.portal__account span:nth-of-type(6)')
        g = re.search("(?P<city>.*), (?P<state>PA) (?P<zipcode>[0-9]{5})", city_state_zip)

        address = Address(
            None,
            street_1,
            None,
            g.group('city'),
            g.group('state'),
            g.group('zipcode')
        )
        accounts.append(Account("ColGasPa", account_number, address))

    return accounts

def get_usage(config, download_path):
    session = requests.Session()

    url = "https://myaccount.columbiagaspa.com/login"
    payload = {
        "username": config['username'],
        "password": config['password'],
        "remember": 1
    }
    fetch_cached(session, 'post', url, data=payload, headers=headers)
    accounts = all_acounts(session)
    results = []
    for account in accounts:
        readings = extract_readings(session, account)
        bills = extract_bills(session, account)
        #payments = extract_payments(bs)
        for bill in bills:
            download_bill(session, account, bill, download_path)
        results.append({
            'account': account, 
            'usage': readings,
            'bills': bills,
        })
    return results 

def extract_bills(session, account):
    url = "https://myaccount.columbiagaspa.com/bills"
    text = fetch_cached(session, 'get', url, headers=headers)
    bs = BeautifulSoup(text, "lxml")
    data = extract_vue_table(bs)
    if data is None:
        return

    bills = []
    for row in data:
        if row['SomethingElse'] != 'Bill':
            continue
        due_date_tuple = re.search('(\d{4})-(\d{2})-(\d{2})', row['Description']).groups()
        due_date_tuple = [int(due_date_tuple[i]) for i in range(len(due_date_tuple))]

        bills.append(Bill(
            row['BillId'],
            parse_iso_date(row['Date']),
            datetime(due_date_tuple[0], due_date_tuple[1], due_date_tuple[2]),
            row['Amount'],
            None,
            None,
            f"https://myaccount.columbiagaspa.com{row['UrlLink']}"
        ))

    print([str(x) for x in bills])
    return bills

def filename_base_for_downloaded_bill(account, bill, download_path):
    return download_path + '/columbiagaspa/ColGasPa_' + str(account.account_number) + '_' + bill.bill_date.strftime('%Y-%m-%d')

def has_downloaded_bill(fn):
    files = glob.glob(fn + "*")
    return len(files) != 0

def download_bill(session, account, bill, download_path):
    fn = filename_base_for_downloaded_bill(account, bill, download_path) + ".pdf"
    if not has_downloaded_bill(fn):
        print("downloaded " + bill.pdf_url + " to " + fn)
        r = session.get(bill.pdf_url, headers=headers)

        directory = os.path.dirname(os.path.abspath(fn))
        if not os.path.exists(directory):
            os.mkdir(directory)
        with open(fn, 'wb') as f:
            f.write(r.content)
        return fn
    print("already downloaded " + bill.pdf_url + " to " + fn)
    return fn

def extract_readings(session, account):
    readings = []
    url = "https://myaccount.columbiagaspa.com/usage"
    text = fetch_cached(session, 'get', url, headers=headers)
    bs = BeautifulSoup(text, "lxml")

    meter_type = select_single(bs, '.meter-data li:nth-of-type(4)')
    meter_type = meter_type.replace('Meter Type', '').strip()


    data = extract_vue_table(bs)
    if data is None:
        return

    for row in data:
        readings.append(Reading(
            parse_iso_date(row['readDate']),
            row['unitsUsed'],
            'Thm',
            row['meterId'],
            meter_type
        ))
    return readings
