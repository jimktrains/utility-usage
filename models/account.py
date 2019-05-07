#!/usr/bin/env python3

class Account:
    def __init__(self, provider, account_number, service_address):
        self.provider = provider
        self.account_number = account_number
        self.service_address = service_address
    def __str__(self):
        return f"{self.provider}:{self.account_number}"
