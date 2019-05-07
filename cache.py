#!/usr/bin/env python3

import sqlite3
import json
from hashlib import sha1
import os
from datetime import datetime
from datetime import timedelta 

def fetch_cached(session, method, url, params=None, data=None, headers=None, cache_ttl=None):
    flush_cache()
    param_to_hash = json.dumps(params).encode('utf8')
    param_hash = sha1(param_to_hash).hexdigest()
    cache_key = f"{url}|{method}|{param_hash}"
    r = cache_get(cache_key)

    if r is not None:
        return r

    print(f"{method} {url} {param_to_hash}")
    r = session.request(method, url, params=params, data=data, headers=headers)

    if r is None:
        return None

    text = r.text

    if cache_ttl is None:
        cache_ttl = timedelta(hours=1)
    one_hour_more = datetime.utcnow() + cache_ttl
    cache_until(cache_key, text, one_hour_more)
    return text

def cache_until(key, value, exp):
    t = (key, value, exp)
    cache_db.execute("insert or replace into cache (cache_key, cache_value, expires_at) values (?,?,?)", t)
    cache_db.commit()

def cache_get(key):
    flush_cache()
    for row in cache_db.execute("select cache_value from cache where cache_key = ?", (key,)):
        return row[0]

def flush_cache():
    cache_db.execute("delete from cache where current_timestamp > expires_at")
    cache_db.commit()

cache_db_file = 'cache.sqlite3'
if not os.path.exists(cache_db_file):
    cache_db = sqlite3.connect(cache_db_file)
    cache_db.execute("create table cache (" + 
                     "cache_key varchar(250) primary key, " + 
                     "cache_value text not null, " + 
                     "expires_at datetime not null)")
    cache_db.commit()
else:
    cache_db = sqlite3.connect(cache_db_file)
