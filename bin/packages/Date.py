#!/usr/bin/python3

import datetime
import time
from calendar import monthrange

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

def get_today_date_str(separator=False):
    if separator:
        return datetime.date.today().strftime("%Y/%m/%d")
    else:
        return datetime.date.today().strftime("%Y%m%d")

def get_current_week_day():
    dt = datetime.date.today()
    start = dt - datetime.timedelta(days=dt.weekday())
    return start.strftime("%Y%m%d")

def get_current_utc_full_time():
    timestamp = datetime.datetime.fromtimestamp(time.time())
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def get_month_dates(date=None):
    if date:
        date = convert_date_str_to_datetime(date)
    else:
        date = datetime.date.today()
    num_days = monthrange(date.year, date.month)[1]
    return [datetime.date(date.year, date.month, day).strftime("%Y%m%d") for day in range(1, num_days+1)]

def get_date_week_by_date(date):
    dt = datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8]))
    start = dt - datetime.timedelta(days=dt.weekday())
    return start.strftime("%Y%m%d")

def date_add_day(date, num_day=1):
    new_date = datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8])) + datetime.timedelta(num_day)
    new_date = str(new_date).replace('-', '')
    return new_date

def daterange_add_days(date, nb_days):
    end_date = date_add_day(date, num_day=nb_days)
    return get_daterange(date, end_date)

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

def get_nb_days_by_daterange(date_from, date_to):
    date_from = datetime.date(int(date_from[0:4]), int(date_from[4:6]), int(date_from[6:8]))
    date_to = datetime.date(int(date_to[0:4]), int(date_to[4:6]), int(date_to[6:8]))
    delta = date_to - date_from # timedelta
    return len(range(delta.days + 1))

def get_date_range_today(date_from):
    return substract_date(date_from, get_today_date_str())

def substract_date(date_from, date_to):
    date_from = datetime.date(int(date_from[0:4]), int(date_from[4:6]), int(date_from[6:8]))
    date_to = datetime.date(int(date_to[0:4]), int(date_to[4:6]), int(date_to[6:8]))
    delta = date_to - date_from # timedelta
    l_date = []
    for i in range(delta.days + 1):
        date = date_from + datetime.timedelta(i)
        l_date.append( date.strftime('%Y%m%d') )
    return l_date

def get_daterange(date_from, date_to):
    date_from = datetime.date(int(date_from[0:4]), int(date_from[4:6]), int(date_from[6:8]))
    date_to = datetime.date(int(date_to[0:4]), int(date_to[4:6]), int(date_to[6:8]))
    delta = date_to - date_from  # timedelta
    l_date = []
    for i in range(delta.days + 1):
        date = date_from + datetime.timedelta(i)
        l_date.append(date.strftime('%Y%m%d'))
    return l_date

def validate_str_date(str_date, separator=''):
    try:
        datetime.datetime.strptime(str_date, '%Y{}%m{}%d'.format(separator, separator))
        return True
    except ValueError:
        return False
    except TypeError:
        return False

def api_validate_str_date_range(date_from, date_to, separator=''):
    is_date = validate_str_date(date_from, separator=separator) and validate_str_date(date_from, separator=separator)
    if not is_date:
        return ({"status": "error", "reason": "Invalid Date"}, 400)
    if int(date_from) > int(date_to):
        return ({"status": "error", "reason": "Invalid Date range, Date from > Date to"}, 400)

def sanitise_date_range(date_from, date_to, separator='', date_type='str'):
    '''
    Check/Return a correct date_form and date_to
    '''
    if not date_from and date_to:
        date_from = date_to
    elif not date_to and date_from:
        date_to = date_from
    elif not date_to and not date_from:
        date = datetime.date.today().strftime("%Y%m%d")
        return {"date_from": date, "date_to": date}

    if date_type=='str':
        # remove separators
        if len(date_from) == 10:
            date_from = date_from[0:4] + date_from[5:7] + date_from[8:10]
        if len(date_to) == 10:
            date_to = date_to[0:4] + date_to[5:7] + date_to[8:10]

        if not validate_str_date(date_from, separator=separator):
            date_from = datetime.date.today().strftime("%Y%m%d")
        if not validate_str_date(date_to, separator=separator):
            date_to = datetime.date.today().strftime("%Y%m%d")
    else: # datetime
        if isinstance(date_from, datetime.datetime):
            date_from = date_from.strftime("%Y%m%d")
        else:
            date_from = datetime.date.today().strftime("%Y%m%d")
        if isinstance(date_to, datetime.datetime):
            date_to = date_to.strftime("%Y%m%d")
        else:
            date_to = datetime.date.today().strftime("%Y%m%d")

    if int(date_from) > int(date_to):
        res = date_from
        date_from = date_to
        date_to = res
    return {"date_from": date_from, "date_to": date_to}

def sanitise_daterange(date_from, date_to, separator='', date_type='str'):
    '''
    Check/Return a correct date_form and date_to
    '''
    if not date_from and date_to:
        date_from = date_to
    elif not date_to and date_from:
        date_to = date_from
    elif not date_to and not date_from:
        date = datetime.date.today().strftime("%Y%m%d")
        return date, date

    if date_type == 'str':
        # remove separators
        if len(date_from) == 10:
            date_from = date_from[0:4] + date_from[5:7] + date_from[8:10]
        if len(date_to) == 10:
            date_to = date_to[0:4] + date_to[5:7] + date_to[8:10]

        if not validate_str_date(date_from, separator=separator):
            date_from = datetime.date.today().strftime("%Y%m%d")
        if not validate_str_date(date_to, separator=separator):
            date_to = datetime.date.today().strftime("%Y%m%d")
    else:  # datetime
        if isinstance(date_from, datetime.datetime):
            date_from = date_from.strftime("%Y%m%d")
        else:
            date_from = datetime.date.today().strftime("%Y%m%d")
        if isinstance(date_to, datetime.datetime):
            date_to = date_to.strftime("%Y%m%d")
        else:
            date_to = datetime.date.today().strftime("%Y%m%d")

    if int(date_from) > int(date_to):
        res = date_from
        date_from = date_to
        date_to = res
    return date_from, date_to

def get_previous_month_date():
    now = datetime.date.today()
    first = now.replace(day=1)
    last_month = first - datetime.timedelta(days=1)
    return last_month.strftime("%Y%m%d")
