#!/usr/bin/env python3

from bs4 import BeautifulSoup
from cache import fetch_cached
from datetime import datetime
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

def parse_slash_date(date):
    return datetime.strptime(date, "%m/%d/%Y")

def all_acounts(session):
    url = "https://wss.amwater.com/selfservice-web/accountSummary.do"
    text = fetch_cached(session, "get", url, headers=headers)
    bs = BeautifulSoup(text, "lxml")
    SERVICE_ADDRESS_IDX=0
    CITY_IDX=1
    STATE_IDX=2
    ZIP_IDX=3
    ACCOUNT_NUMBER_IDX=4
    BALANCE_IDX=5
    DUE_DATE_IDX=6
    accounts = []
    for row in bs.select('#individualAccountsTable'):

        cells = row.select('td')
        if len(cells) < 7:
            continue

        address = Address(
            cells[SERVICE_ADDRESS_IDX].text.strip(),
            None,
            cells[CITY_IDX].text,
            cells[STATE_IDX].text,
            cells[ZIP_IDX].text,
            None
        )
        accounts.append(Account("AMWater", cells[ACCOUNT_NUMBER_IDX].text, address))

    return accounts

def get_usage(config, download_path):
    session = requests.Session()

    url = "https://wss.amwater.com/selfservice-web/processLogin.do"
    payload = {
            'loginReferrer': 'login',
            'action': '',
            'j_username': config['username'],
            'j_password': config['password'],
        }
    fetch_cached(session, 'post', url, data=payload, headers=headers)
    accounts = all_acounts(session)
    results = []
    for account in accounts:
        bs = switch_account(session, account)
        readings = extract_readings(session, account)
        bills = extract_bills(session, account)
        payments = extract_payments(bs)
        for bill in bills:
            download_bill(session, account, bill, download_path)
        results.append({
            'account': account, 
            'usage': readings,
            'bills': bills,
        })
    return results 

def switch_account(session, account):
    url = "https://wss.amwater.com/selfservice-web/accountDetail.do"
    payload = {
        'accountNumber': account.account_number
    }
    text = fetch_cached(session, 'post', url, data=payload, headers=headers)
    bs = BeautifulSoup(text, 'lxml')
    return bs

def extract_payments(bs):
    TX_DATE_IDX=0
    TX_TYPE_IDX=1
    IMPORTANT_INFORMATION_IDX=2
    AMOUNT_IDX=3
    BALANCE_IDX=4

    payments = []
    for row in bs.select('#transactionActivityTable tr'):
        cells = row.select('td')
        if len(cells) < 5:
            continue
        if 'View Bill' not in cells[TX_TYPE_IDX].text:
            payment_date = datetime.strptime(cells[TX_DATE_IDX].text, "%m/%d/%Y")
            payments.append({
                'payment_date': payment_date,
                'amount': cells[AMOUNT_IDX].text,
                'balance': cells[BALANCE_IDX].text,
                'meta': {
                    'important_information': cells[IMPORTANT_INFORMATION_IDX].text.strip(),
                    'balance': cells[BALANCE_IDX].text,
                 },
            })
    return payments

def extract_bills(session, account):
    TX_DATE_IDX=0
    TX_TYPE_IDX=1
    IMPORTANT_INFORMATION_IDX=2
    AMOUNT_IDX=3
    BALANCE_IDX=4

    url = "https://wss.amwater.com/selfservice-web/accountDetailActivity.do"
    params = {
        "accountNumber": account.account_number,
        "activityRange": 24
    }
    text = fetch_cached(session, 'post', url, data=params, headers=headers)
    bs = BeautifulSoup(text, "lxml")

    bills = []
    for row in bs.select('#transactionActivityTable tr'):
        cells = row.select('td')
        if len(cells) < 5:
            continue
        if 'View Bill' in cells[TX_TYPE_IDX].text:
            bill_date = cells[TX_DATE_IDX].text.split('/')
            bill_date = bill_date[2] + '-' + bill_date[1] + '-' + bill_date[0]
            bills.append(Bill(
                None,
                parse_slash_date(cells[TX_DATE_IDX].text), 
                parse_slash_date(cells[TX_DATE_IDX].text), 
                cells[AMOUNT_IDX].text, 
                cells[BALANCE_IDX].text, 
                cells[IMPORTANT_INFORMATION_IDX].text.strip(),
                # Adding a / to the end of the prefix makes the path have two /s
                # which is normally fine, but it invalidates the session?
                "https://wss.amwater.com" + cells[TX_TYPE_IDX].select('a')[0]['href']
            ))
    return bills

def filename_base_for_downloaded_bill(account, bill, download_path):
    return download_path + '/amwater/AM-Water_' + str(account.account_number) + '_' + bill.bill_date.strftime('%Y-%m-%d')

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
    READ_DATE_IDX = 0
    BILL_DATE_IDX = 1
    USAGE_IDX = 2
    UNITS_IDX = 3
    ACCOUNT_NUMBER_IDX = 5
    METER_NUMBER_IDX = 6
    SERVICE_TYPE_IDX = 7
    readings = []
    url = "https://wss.amwater.com/selfservice-web/accountDetailUsage.do"
    params = {
        "accountNumber": account.account_number,
        "usageRange": 24
    }
    text = fetch_cached(session, 'post', url, data=params, headers=headers)
    bs = BeautifulSoup(text, "lxml")
    for row in bs.select('#usageActivityTable tr'):
        cells = row.select('td')
        if (len(cells) < 8):
            continue
        readings.append(Reading(
            parse_slash_date(cells[READ_DATE_IDX].text),
            cells[USAGE_IDX].text,
            cells[UNITS_IDX].text,
            cells[METER_NUMBER_IDX].text,
            cells[SERVICE_TYPE_IDX].text
        ))
    return readings
