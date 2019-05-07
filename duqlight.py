#!/usr/bin/env python3

import requests
import glob
from cache import fetch_cached
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from models.reading import Reading
from models.bill import Bill
from models.account import Account
from models.address import Address

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0',
}

def all_acounts(session):
    url = "https://www.duquesnelight.com/account-billing/account-summary/GetAccounts"
    text = fetch_cached(session, 'get', url, headers=headers)

    alldata = json.loads(text)

    if alldata['Success']:
        alldata = alldata['Payload']
    accounts = []
    
    for account in alldata['AllAccounts']:
        premise = account['PremiseAddress']
        address = premise['Address']
        address = Address(
            address['Line1'],
            address['Line2'],
            address['City'],
            address['State'],
            address['Zip1'],
            premise['Id']
        )
        accounts.append(Account('DuqueseLight', account['AccountNumber'], address))
    return accounts

def get_usage(config):
    session = requests.Session()

    url = "https://www.duquesnelight.com/Home/login"
    payload = {
            'Username':	config['username'],
            'Password':	config['password'],
            'RememberUsername':	False,
            'RedirectUrl': '/energy-money-savings/my-electric-use',
            'SuppressPleaseLoginMessage': False
        }
    text = fetch_cached(session, 'post', url, data=payload, headers=headers)
    accounts = all_acounts(session)
    results = []
    for account in accounts:
        readings = extract_readings(session, account)
        bills = extract_bills(session, account)
        for bill in bills:
            download_bill(session, account, bill)
        results.append({
            'account': account,
            'usage': readings,
            'bills': bills,
        })
    return results


def extract_for_account(session, account):
    readings = extract_readings(session, account)
    bills = extract_bills(session, account)
    return {
        'readings': readings,
        'bills': bills,
    }

def extract_bills(session, account):
    url = "https://www.duquesnelight.com/account-billing/account-summary/GetBillHistory/"
    text = fetch_cached(session, 'get', url, headers=headers)
    raw_bills = json.loads(text)
    if raw_bills['Success']:
        raw_bills = raw_bills['Payload']
    bills = []
    for bill in raw_bills:
        bills.append(DLBill(
            bill['Id'],
            parse_asp_net_json_datetime(bill['Date']),
            parse_asp_net_json_datetime(bill['DueDate']),
            bill['AmountDue'],
            bill['AccountBalance'],
            bill['PdfHash']
        ))
    return bills

def filename_base_for_downloaded_bill(account, bill):
    an = str(account.account_number)
    bd = bill.bill_date.strftime('%Y-%m-%d')
    return f"DuquesneLight_{an}_{bd}"

def has_downloaded_bill(account, bill):
    files = glob.glob(filename_base_for_downloaded_bill(account, bill) + "*")
    return len(files) != 0

def download_bill(session, account, bill):
    fn = filename_base_for_downloaded_bill(account, bill) + ".pdf"
    print("would have downloaded " + bill.pdf_url + " to " + fn)
    # if not has_downloaded_bill(account, bill):
    #     r = fetch_cached(session, 'get', bill['meta']['pdf_url'])
    #     with file(fn, 'w') as f:
    #         f.write(r.content)
    return fn

def parse_asp_net_json_datetime(value):
    """
    http://msdn.microsoft.com/en-us/library/bb299886.aspx#intro_to_json_topic2

    One of the sore points of JSON is the lack of a date/time literal.
    Many people are surprised and disappointed to learn this when they
    first encounter JSON. The simple explanation (consoling or not) for
    the absence of a date/time literal is that JavaScript never had one
    either: The support for date and time values in JavaScript is
    entirely provided through the Date object. Most applications using
    JSON as a data format, therefore, generally tend to use either a
    string or a number to express date and time values. If a string is
    used, you can generally expect it to be in the ISO 8601 format. If a
    number is used, instead, then the value is usually taken to mean the
    number of milliseconds in Universal Coordinated Time (UTC) since
    epoch, where epoch is defined as midnight January 1, 1970 (UTC).
    Again, this is a mere convention and not part of the JSON standard.
    If you are exchanging data with another application, you will need
    to check its documentation to see how it encodes date and time
    values within a JSON literal. For example, Microsoft's ASP.NET AJAX
    uses neither of the described conventions. Rather, it encodes .NET
    DateTime values as a JSON string, where the content of the string is
    /Date(ticks)/ and where ticks represents milliseconds since epoch
    (UTC). So November 29, 1989, 4:55:30 AM, in UTC is encoded as
    "\/Date(628318530718)\/".
    """
    g = re.search("(\d+)", value).groups()
    date = None,
    if len(g) == 1:
        millis = g[0]
        date = datetime.fromtimestamp((int(millis))/1000.0)
    return date

def extract_readings(session, account):
    url = "https://www.duquesnelight.com/account-billing/account-summary/usage-summary/GetUsage/"
    params = {
        'premiseId': account.service_address.util_id
    }
    text = fetch_cached(session, 'get', url, params=params, headers=headers)
    raw_readings = json.loads(text)
    if raw_readings['Success']:
        raw_readings = raw_readings['Payload']

    readings = []
    for reading in raw_readings:
        read_date = parse_asp_net_json_datetime(reading['ReadDate'])
        readings.append(Reading(read_date, reading['Read'], reading['UnitOfMeasure'], None, None))
    return readings

class DLBill(Bill):
    def __init__(self, util_id, bill_date, due_date, amount, balance, pdf_hash):
        super().__init__(util_id, bill_date, due_date, amount, balance)
        self.pdf_url = f"https://www.duquesnelight.com/account-billing/account-summary/DownloadBillPdf/{pdf_hash}"
