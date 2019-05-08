#!/usr/bin/env python3

class Bill:
    def __init__(self, util_id, bill_date, due_date, amount, balance, important_information=None, pdf_url=None):
        self.util_id = util_id
        self.bill_date = bill_date
        self.due_date = due_date
        self.amount = amount
        self.balance = balance
        self.important_information = important_information
        self.pdf_url = pdf_url
    def __str__(self):
        date = self.bill_date.strftime("%Y-%m-%d")
        due = self.due_date.strftime("%Y-%m-%d")
        return f"{self.amount}@{date} Due:{due} Balance:{self.balance} {self.important_information}"
