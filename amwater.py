#!/usr/bin/env python3

import requests
import glob
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0',
}

def all_acounts(session):
    url = "https://wss.amwater.com/selfservice-web/accountSummary.do"
    #r = session.get(url, headers=headers)
    #text = r.text
    text = None
    with open('am_cache_all_accounts') as f:
        text = f.read()
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

        accounts.append({
            'service_address': {
                'street': cells[SERVICE_ADDRESS_IDX].text.strip(),
                'city': cells[CITY_IDX].text,
                'state': cells[STATE_IDX].text,
                'zip': cells[ZIP_IDX].text,
            },
            'account_number': cells[ACCOUNT_NUMBER_IDX].text,
        })

    return accounts

def get_usage(config):
    session = requests.Session()

    url = "https://wss.amwater.com/selfservice-web/processLogin.do"
    #url = "https://httpbin.org/cookies/set/a/1"
    payload = {
            'loginReferrer': 'login',
            'action': '',
            'j_username': config['username'],
            'j_password': config['password'],
        }
    #r = session.post(url, data=payload, headers=headers)
    accounts = all_acounts(session)
    for account in accounts:
        account.update(extract_for_account(session, account['account_number']))
    return accounts


def extract_for_account(session, account_number):
    bs = switch_account(session, account_number)
    readings = extract_readings(bs)
    bills = extract_bills(bs, session)
    payments = extract_payments(bs)
    return {
        'readings': readings,
        'bills': bills,
        'payments': payments,
    }


def switch_account(session, account_number):
    url = "https://wss.amwater.com/selfservice-web/accountDetail.do"
    payload = {
        'accountNumber': account_number
    }
    #r = session.post(url, data=payload, headers=headers)
    #text = r.text
    with open('am_cache') as f:
        text = f.read()
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
            payments.append({
                'payment_date': cells[TX_DATE_IDX].text,
                'amount': cells[AMOUNT_IDX].text,
                'balance': cells[BALANCE_IDX].text,
                'meta': {
                    'important_information': cells[IMPORTANT_INFORMATION_IDX].text.strip(),
                    'balance': cells[BALANCE_IDX].text,
                 },
            })
    return payments

def extract_bills(bs, session):
    TX_DATE_IDX=0
    TX_TYPE_IDX=1
    IMPORTANT_INFORMATION_IDX=2
    AMOUNT_IDX=3
    BALANCE_IDX=4

    bills = []
    for row in bs.select('#transactionActivityTable tr'):
        cells = row.select('td')
        if len(cells) < 5:
            continue
        if 'View Bill' in cells[TX_TYPE_IDX].text:
            bill_date = cells[TX_DATE_IDX].text.split('/')
            bill_date = bill_date[2] + '-' + bill_date[1] + '-' + bill_date[0]
            account_number = bs.select('nav#menuBar')[0]['data-accountnumber']
            url = "https://wss.amwater.com/" + cells[TX_TYPE_IDX].select('a')[0]['href']
            download_bill(account_number, bill_date, url, session)
            bills.append({
                'bill_date': cells[TX_DATE_IDX].text,
                'amount': cells[AMOUNT_IDX].text,
                'balance': cells[BALANCE_IDX].text,
                'meta': {
                    'important_information': cells[IMPORTANT_INFORMATION_IDX].text.strip(),
                    'balance': cells[BALANCE_IDX].text,
                 },
            })
    return bills

def filename_base_for_downloaded_bill(account_number, date):
    return 'AM-Water_' + str(account_number) + '_' + str(date)

def has_downloaded_bill(account_number, date):
    files = glob.glob(filename_base_for_downloaded_bill(account_number, date) + "*")
    return len(files) != 0

def download_bill(account_number, date, url, session):
    fn = filename_base_for_downloaded_bill(account_number, date) + ".pdf"
    print("would have downloaded " + url + " to " + fn)
    # r = session.get(url)
    # with file(fn, 'w') as f:
    #     f.write(r.content)
    return fn

def extract_readings(bs):
    READ_DATE_IDX = 0
    BILL_DATE_IDX = 1
    USAGE_IDX = 2
    UNITS_IDX = 3
    ACCOUNT_NUMBER_IDX = 5
    METER_NUMBER_IDX = 6
    SERVICE_TYPE_IDX = 7
    readings = []
    for row in bs.select('#usageActivityTable tr'):
        cells = row.select('td')
        if (len(cells) < 8):
            continue
        readings.append({
            'usage': cells[USAGE_IDX].text,
            'units': cells[UNITS_IDX].text,
            'read_date': cells[READ_DATE_IDX].text,
            'bill_date': cells[BILL_DATE_IDX].text,
            'meta': {
                'meter_number': cells[METER_NUMBER_IDX].text,
                'service_type': cells[SERVICE_TYPE_IDX].text,
            },
        })
    return readings
