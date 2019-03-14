#!/usr/bin/env python3

import amwater
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

am_water_usage = amwater.get_usage(config['amwater'])

print(am_water_usage)
