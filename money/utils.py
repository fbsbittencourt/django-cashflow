import datetime
from money import settings

def last_day_of_this_month(date):
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(day=1, month=date.month+1) - datetime.timedelta(days=1)

def single_date_range_string(date_reference = None, days=0):
    if not date_reference:
        date_reference = datetime.date.today()

    date_reference+=datetime.timedelta(days=days)

    return date_reference.strftime(settings.DATE_FORMAT) + ";" + date_reference.strftime(settings.DATE_FORMAT)

def date_shortcuts():
    output = [
        (single_date_range_string(), 'Today'),
        (single_date_range_string(days=-1), 'Yesterday'),
        (single_date_range_string(days=+1), 'Tomorrow'),
    ]

    return output
