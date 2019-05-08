#!/usr/bin/env python3

import os
import sqlite3

db = None
def init(download_path):
    global db
    db_file = download_path + "/data.sqlite3" 
    if not os.path.exists(db_file):
        db = sqlite3.connect(db_file)
        db.execute("create table address(" + 
                         "id integer primary key autoincrement, " + 
                         "street_1 varchar(255) not null, " + 
                         "street_2 varchar(255) not null, " + 
                         "city varchar(255) not null, " + 
                         "state varchar(255) not null, " + 
                         "zipcode varchar(255) not null, " +
                         "unique(street_1, street_2, city, state, zipcode) " + 
                         ")")
        db.execute("create table account (" + 
                         "id integer primary key autoincrement, " + 
                         "provider varchar(255) not null, " + 
                         "account_number varchar(255) not null, " + 
                         "service_address_id integer references address(id), " + 
                         "unique(provider, account_number) " + 
                         ")")
        db.execute("create table usage (" + 
                         "id integer primary key autoincrement, " + 
                         "account_id integer references account(id), " +
                         "reading real not null, " +
                         "uom varchar(255) not null, " +
                         "date datetime not null, " + 
                         "meter_number varchar(255), " + 
                         "service_type varchar(255), " + 
                         "unique(account_id, uom, date) " +
                         ")")
        db.execute("create table bill (" + 
                         "id integer primary key autoincrement, " + 
                         "account_id integer references account(id), " +
                         "amount real not null, " +
                         "balance real not null, " +
                         "date datetime not null, " + 
                         "due_date datetime not null, " + 
                         "pdf_url text, " + 
                         "important_information text, " + 
                         "unique(account_id, date)" + 
                         ")")
        db.commit()
    else:
        db = sqlite3.connect(db_file)

def insert_or_find_record(insert_sql, insert_tuple, select_sql, select_tuple):
    cur = db.execute(insert_sql, insert_tuple)
    db.commit()

    # cur.lastrowid gives very odd results with insert or ignore
    result = db.execute(select_sql, select_tuple)
    for row in result:
        return row[0]

def insert_address(address):
    address_tuple = (
        address.street_1,
        # this is not null because then otherwise it'll allow multiple 
        # otherwise identicle rows with a null value here
        address.street_2 or '',
        address.city,
        address.state,
        address.zipcode
    )
    insert_sql = ("insert or ignore into address (street_1, street_2, city, state, zipcode) " + 
                                         "values (?       , ?       , ?   , ?    , ?)");
    select_sql = ("select id from address where " + 
                  "   street_1 = ? and street_2 = ? and " + 
                  "   city = ? and state = ? and zipcode = ?")
    return insert_or_find_record(insert_sql, address_tuple, select_sql, address_tuple)
        

def insert_account(account):
    address_id  = insert_address(account.service_address)

    insert_sql = ("insert or ignore into account (provider, account_number, service_address_id) " +
                                         "values (?       , ?             , ?)")
    select_sql = ("select id from account where provider = ? and account_number = ?")

    account_tuple = (
        account.provider,
        account.account_number,
        address_id
    )

    select_tuple = (
        account.provider,
        account.account_number
    )

    return insert_or_find_record(insert_sql, account_tuple, select_sql, select_tuple)

def insert_usage(account_dbid, usage):
    insert_sql = ("insert or ignore into usage(account_id, reading, uom, date, meter_number, service_type) " + 
                                         "values (?      , ?      , ?  , ?   , ?           , ?)")
    select_sql = "select id from usage where account_id = ? and uom = ? and date = ?"

    usage_tuple = (
        account_dbid,
        usage.usage,
        usage.uom,
        usage.date,
        usage.meter_number,
        usage.service_type
    )

    select_tuple = (
        account_dbid,
        usage.uom,
        usage.date
    )

    return insert_or_find_record(insert_sql, usage_tuple, select_sql, select_tuple)

def insert_bill(account_dbid, bill):
    insert_sql = ("insert or ignore into bill(account_id, amount, balance, date, due_date, pdf_url, important_information) " +
                                         "values (?      , ?     , ?      , ?   , ?       , ?      , ?)")
    select_sql = "select id from bill where account_id = ? and date = ?"

    usage_tuple = (
        account_dbid,
        bill.amount,
        bill.balance,
        bill.bill_date,
        bill.due_date,
        bill.pdf_url,
        bill.important_information
    )

    select_tuple = (
        account_dbid,
        bill.bill_date
    )

    return insert_or_find_record(insert_sql, usage_tuple, select_sql, select_tuple)
