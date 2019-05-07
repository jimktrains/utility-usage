#!/usr/bin/env python3

class Reading:
    def __init__(self, date, usage, uom, meter_number, service_type):
        self.date = date
        self.usage = usage
        self.uom = uom
        self.meter_number = meter_number
        self.service_type = service_type
    def __str__(self):
        date = self.date.strftime("%Y-%m-%d")
        return f"{self.usage}{self.uom}@{date}"
