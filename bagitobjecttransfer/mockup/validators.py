from datetime import datetime
from calendar import monthrange, month_name
import re

from django.core.exceptions import ValidationError


FULL_DATE = re.compile(r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<date>\d{2})$')
SINGLE_YEAR = re.compile(r'(?P<year>^\d{4})$')


def validate_date(value):
    # Validating Single Year
    match_obj = SINGLE_YEAR.match(value)
    if match_obj:
        year = int(match_obj.group('year'))
        if year < 1000:
            raise ValidationError(
                f'Any year before the year 1000 is not allowed. Year {year} is too low'
            )
        else:
            return

    # Validating yyyy-mm-dd
    match_obj = FULL_DATE.match(value)
    if not match_obj:
        raise ValidationError('Date did not match yyyy-mm-dd format')

    year = int(match_obj.group('year'))
    month = int(match_obj.group('month'))
    date = int(match_obj.group('date'))
    today = datetime.now()

    if year < 1000:
        raise ValidationError(
            f'Any year before the year 1000 is not allowed. Year {year} is too low'
        )

    if month == 0:
        raise ValidationError(
            f'The month number cannot be "00"'
        )

    if month > 12:
        raise ValidationError(
            f'The month number cannot be greater than 12. {month} is too high'
        )

    _, days_in_month = monthrange(year, month)

    if date == 0:
        raise ValidationError(
            f'The date number cannot be "00"'
        )

    if date > days_in_month:
        if year < today.year or year == today.year and month < today.month:
            raise ValidationError(
                f'There were only {days_in_month} days in {month_name[month]}, {year}. '
                f'{date} is too high'
            )
        elif year == today.year and month == today.month:
            raise ValidationError(
                f'There are only {days_in_month} days this month. {date} is too high'
            )
        else:
            raise ValidationError(
                f'There are only {days_in_month} days in {month_name[month]}, {year}. '
                f'{date} is too high'
            )

    date_obj = datetime(year, month, date, 0, 0, 0)

    if date_obj > today:
        raise ValidationError(
            f'Dates in the future are not allowed'
        )
