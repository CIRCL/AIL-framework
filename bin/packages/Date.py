#!/usr/bin/python3

import datetime

from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

def convert_date_str_to_datetime(date_str):
    res =  datetime.date(int(date_str[0:4]), int(date_str[4:6]), int(date_str[6:8]))
    return res

def get_full_month_str(date_from, date_to):
    # add one day (if last day of the month)
    date_to = date_to + relativedelta(days=+1)
    full_month = [dt for dt in rrule(MONTHLY, bymonthday=1,dtstart=date_from, until=date_to)]
    # remove last_month (incomplete)
    if len(full_month):
        full_month = full_month[:-1]
    return full_month

def get_date_range_full_month_and_days(date_from, date_to):
    date_from = convert_date_str_to_datetime(date_from)
    date_to = convert_date_str_to_datetime(date_to)

    full_month = get_full_month_str(date_from, date_to)

    # request at least one month
    if full_month:
        day_list = substract_date(date_from.strftime('%Y%m%d'), full_month[0].strftime('%Y%m%d'))
        # remove last day (day in full moth)
        if day_list:
            day_list = day_list[:-1]
        day_list.extend(substract_date( (full_month[-1] + relativedelta(months=+1) ).strftime('%Y%m%d'), date_to.strftime('%Y%m%d')))
    else:
        day_list = substract_date(date_from.strftime('%Y%m%d'), date_to.strftime('%Y%m%d'))

    full_month = [dt_month.strftime('%Y%m') for dt_month in full_month]
    return day_list, full_month

# # TODO: refractor me

class Date(object):
    """docstring for Date"""
    def __init__(self, *args):
        if len(args) == 3:
            self.year = str(args[0])
            self.month = str(args[1])
            self.day = str(args[2]).zfill(2)
        if len(args) == 1:
            self.year = str(args[0])[:4]
            self.month = str(args[0])[4:6]
            self.day = str(args[0])[6:]

    def __str__(self):
        return "{0}{1}{2}".format(self.year, self.month, self.day)

    def _get_year(self):
        return self.year

    def _get_month(self):
        return self.month

    def _get_day(self):
        return self.day

    def _set_year(self, year):
        self.year = year

    def _set_month(self, month):
        self.month = month

    def _set_day(self, day):
        self.day = day

    def substract_day(self, numDay):
        computed_date = datetime.date(int(self.year), int(self.month), int(self.day)) - datetime.timedelta(numDay)
        comp_year = str(computed_date.year)
        comp_month = str(computed_date.month).zfill(2)
        comp_day = str(computed_date.day).zfill(2)
        return comp_year + comp_month + comp_day

def get_today_date_str():
    return datetime.date.today().strftime("%Y%m%d")

def date_add_day(date, num_day=1):
    new_date = datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8])) + datetime.timedelta(num_day)
    new_date = str(new_date).replace('-', '')
    return new_date

def date_substract_day(date, num_day=1):
    new_date = datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8])) - datetime.timedelta(num_day)
    new_date = str(new_date).replace('-', '')
    return new_date

# # TODO: remove me ## FIXME:
def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))
    return list(reversed(date_list))

def get_previous_date_list(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []
    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))
    return list(reversed(date_list))

def substract_date(date_from, date_to):
    date_from = datetime.date(int(date_from[0:4]), int(date_from[4:6]), int(date_from[6:8]))
    date_to = datetime.date(int(date_to[0:4]), int(date_to[4:6]), int(date_to[6:8]))
    delta = date_to - date_from # timedelta
    l_date = []
    for i in range(delta.days + 1):
        date = date_from + datetime.timedelta(i)
        l_date.append( date.strftime('%Y%m%d') )
    return l_date

def validate_str_date(str_date, separator=''):
    try:
        datetime.datetime.strptime(str_date, '%Y{}%m{}%d'.format(separator, separator))
        return True
    except ValueError:
        return False

def sanitise_date_range(date_from, date_to, separator=''):
    '''
    Check/Return a correct date_form and date_to
    '''
    if not validate_str_date(date_from, separator=separator):
        date_from = datetime.date.today().strftime("%Y%m%d")
    if not validate_str_date(date_to, separator=separator):
        date_to = datetime.date.today().strftime("%Y%m%d")

    if int(date_from) > int(date_to):
        date_from = date_to
    return {"date_from": date_from, "date_to": date_to}
