''' AtoM-specific date parsing.

AtoM CSV templates have three columns for dates: eventDates, eventStartDates, and eventEndDates.
The EventDateParser class handles parsing the dates in each of those three columns and returns
clean, uniformly-formatted dates to be used to update each of those columns.
'''
from abc import ABC, abstractmethod
from calendar import monthrange
import calendar
import datetime
import re

import dateparser


class UnknownDateFormat(Exception):
    ''' Raised if a date cannot be parsed
    '''


def split_by(string, split_char):
    ''' Split a string into an array by arbitrary character.

    Args:
        string (str): The string to split
        split_char (str): The character to split the string by

    Returns:
        (list): A list of strings split by the split_char
    '''
    items = []
    if string is None:
        return items
    for sub in string.split(split_char):
        sub_clean = sub.strip()
        if sub_clean:
            items.append(sub_clean)
    return items


def cardinality(string):
    ''' Determine the cardinality of a string. If a string is empty or Falsy, its cardinality is
    zero. Otherwise, the cardinality is the number of pipe characters plus one.

    Args:
        string (str): The string to calculate cardinality for

    Returns:
        (int): The cardinality of the string
    '''
    if string is None:
        return 0
    elif not string.strip():
        return 0
    return string.count('|') + 1


ABBREV_MONTH_WORDS = list(calendar.month_abbr)
SANITIZE_DATE = re.compile(
    r'(?i)^\s*[{\[\s]*(?:ca\.?|c\.|circa|between)?\s*'
    r'(?P<sanitized>.*?)'
    r'\s*\??\s*[}\]\s]*\s*$')


class EventDateParser:
    ''' eventDates parser for AtoM CSVs
    '''

    def __init__(self, unknown_date='Unknown date', unknown_start_date='1800-01-01',
                 unknown_end_date='2010-01-01', timid=False):
        self.unknown_date = unknown_date
        self.str_unknown_start_date = unknown_start_date
        self.unknown_start_date = datetime.date(*[int(x) for x in unknown_start_date.split('-')])
        self.str_unknown_end_date = unknown_end_date
        self.unknown_end_date = datetime.date(*[int(x) for x in unknown_end_date.split('-')])

        if self.unknown_end_date < self.unknown_start_date:
            # Swap
            self.unknown_start_date, self.unknown_end_date =\
            self.unknown_end_date, self.unknown_start_date
            # Swap
            self.str_unknown_start_date, self.str_unknown_end_date =\
            self.str_unknown_end_date, self.str_unknown_start_date

        init_vars = (self.unknown_date, self.unknown_start_date, self.unknown_end_date)
        self.parser = UnknownDateHandler(*init_vars)
        final_parser = self.parser.set_next(YearRangeHandler(*init_vars))\
            .set_next(YearMonthDayHandler(*init_vars))\
            .set_next(YearMonthRangeHandler(*init_vars))\
            .set_next(YearMonthDayRangeHandler(*init_vars))\
            .set_next(ZeroMonthHandler(*init_vars))\
            .set_next(ZeroDayHandler(*init_vars))\
            .set_next(DecadeHandler(*init_vars))\
            .set_next(DecadeRangeHandler(*init_vars))\
            .set_next(YearHandler(*init_vars))\
            .set_next(SeasonHandler(*init_vars))\
            .set_next(MonthWordYearHandler(*init_vars))\
            .set_next(MonthWordDayYearHandler(*init_vars))\
            .set_next(DayMonthWordYearHandler(*init_vars))\
            .set_next(MonthWordDayYearRangeHandler(*init_vars))\
            .set_next(DateParserHandler(*init_vars))

        if not timid:
            final_parser.set_next(YearAnywhereInDateHandler(*init_vars))

    def parse_date(self, date: str) -> tuple:
        ''' Get parsed date range, and a clean string representation of the date. May raise an
        UnknownDateFormat exception if the date could not be parsed.

        Args:
            date (str): The date string to parse

        Returns:
            (tuple): A two-element tuple. The first element is the clean string version of the date,
                the second element is a list containing the range of dates encompassed by the
                parsed date. For example, if the date was 2000, the date range will be 2000-01-01 to
                2000-12-31. Each date in the second element of the tuple is a datetime.date object.
        '''
        try:
            return self.parser.handle(self._sanitize_date(date))
        except ValueError as exc:
            raise UnknownDateFormat(f'{exc} for {date}') from exc

    def _sanitize_date(self, date: str):
        if date is None:
            return ''
        return SANITIZE_DATE.match(date).group('sanitized')

    def parse_event_dates(self, event_date: str, start_date: str = None, end_date: str = None):
        ''' Parse dates and get well-formatted string dates for each date column.

        Args:
            event_date: The eventDates cell from a row of a CSV
            start_date: The eventStartDates cell from the same row
            end_date: The eventEndDates cell from the same row

        Returns:
            (dict): A fixed-up version of the eventDates, eventStartDates, and eventEndDates
                columns. Each fixed up column is in a similarly-named key of the dictionary, e.g.,
                the fixed eventDates are in the eventDates key.
        '''
        event_date = event_date.strip() if event_date else ''
        start_date = start_date.strip() if start_date else ''
        end_date = end_date.strip() if end_date else ''
        all_dates = (event_date, start_date, end_date)
        if any([cardinality(d) > 1 for d in all_dates]):
            raise ValueError('parse_event_dates does not accept pipe-delimited date cells')
        trivial_result = self._handle_trivial_cases(all_dates)
        if trivial_result:
            return trivial_result
        return self._parse_date_group(event_date, start_date, end_date)

    def _handle_trivial_cases(self, dates):
        if not any(dates) or dates[0] == self.unknown_date:
            return {
                'eventDates': self.unknown_date,
                'eventStartDates': self.str_unknown_start_date,
                'eventEndDates': self.str_unknown_end_date,
            }
        if all([x.lower() in ('', 'null') for x in dates]):
            return {
                'eventDates': 'NULL',
                'eventStartDates': 'NULL',
                'eventEndDates': 'NULL',
            }
        return None

    def _parse_date_group(self, event_date: str, event_start_date: str, event_end_date: str):
        fixed_event_dates = set() # Set of strings
        all_start_end_dates = set() # Set of datetime.date objects

        for date in split_by(event_date, ' and '):
            parsed_date, date_range = self.parse_date(date)
            fixed_event_dates.add(parsed_date)
            for _datetime in date_range:
                all_start_end_dates.add(_datetime)

        curr_min_date = self.get_min_date_avoid_reserved_dates(all_start_end_dates)
        curr_max_date = self.get_max_date_avoid_reserved_dates(all_start_end_dates)
        curr_date_unknown = self.date_is_unknown(curr_min_date, curr_max_date)

        start_end_range = self._get_start_end_date_range(event_start_date, event_end_date)
        start_end_min = start_end_range[0] if start_end_range else curr_min_date
        start_end_max = start_end_range[1] if start_end_range else curr_max_date
        start_end_unknown = self.date_is_unknown(start_end_min, start_end_max)

        if curr_date_unknown and not start_end_unknown:
            curr_min_date = start_end_min
            curr_max_date = start_end_max

        # eventStartDates or eventEndDates fell outside of parsed eventDates
        if start_end_min < curr_min_date or start_end_max > curr_max_date:
            new_start_date = min(curr_min_date, start_end_min)
            new_end_date = max(curr_max_date, start_end_max)
            year_1 = new_start_date.year
            year_2 = new_end_date.year
            new_event_dates = f'{year_1} - {year_2}' if year_1 != year_2 else str(year_1)

        # eventDates encompassed eventStartDates and eventEndDates
        else:
            new_event_dates = self._get_well_formatted_event_dates(fixed_event_dates, curr_min_date,
                                                                   curr_max_date)
            new_start_date = curr_min_date
            new_end_date = curr_max_date

        return {
            'eventDates': new_event_dates,
            'eventStartDates': new_start_date.strftime(r'%Y-%m-%d'),
            'eventEndDates': new_end_date.strftime(r'%Y-%m-%d'),
        }

    def date_is_unknown(self, start_date, end_date):
        return start_date == self.unknown_start_date and end_date == self.unknown_end_date

    def get_min_date_avoid_reserved_dates(self, dates):
        ''' Get the earliest date in a set, avoiding returning unknown dates whenever possible '''
        return self._get_min_max_date_avoid_reserved(min, self.unknown_start_date, dates)

    def get_max_date_avoid_reserved_dates(self, dates):
        ''' Get the latest date in a set, avoiding returning unknown dates whenever possible '''
        return self._get_min_max_date_avoid_reserved(max, self.unknown_end_date, dates)

    def _get_min_max_date_avoid_reserved(self, max_min_function, default, dates):
        if not dates:
            return default
        if len(dates) == 1:
            return next(iter(dates))
        if len(dates) > 1:
            reserved = (self.unknown_start_date, self.unknown_end_date)
            no_reserved_dates = list(filter(lambda d: d not in reserved, dates))
            return max_min_function(no_reserved_dates) if no_reserved_dates else default
        return default

    def _get_start_end_date_range(self, event_start_date: str, event_end_date: str):
        ''' Get the earliest and latest dates represented by the start and end dates. Does not add
        dates in if they are unknown.

        Args:
            event_start_date (str): A single eventStartDate
            event_end_date (str): A single eventEndDate

        Returns:
            (tuple): A tuple containing the earliest date and the latest date, in that order. May be
                None if no dates were found or could be parsed.
        '''
        start_end_dates = set()
        all_dates = set([event_start_date, event_end_date])

        if self.str_unknown_start_date in all_dates and self.str_unknown_end_date in all_dates:
            return None

        for date in all_dates:
            try:
                _, date_range = self.parse_date(date)
                if len(date_range) == 2 and self.date_is_unknown(date_range[0], date_range[1]):
                    continue
                for _datetime in date_range:
                    start_end_dates.add(_datetime)
            except UnknownDateFormat:
                pass

        if not start_end_dates:
            return None

        min_date = min(start_end_dates)
        max_date = max(start_end_dates)

        if self.date_is_unknown(min_date, max_date):
            return None

        return (min_date, max_date)

    def _get_well_formatted_event_dates(self, event_dates: set, min_date: datetime.date,
                                        max_date: datetime.date):
        ''' Creates a clean string representation of the event_dates set.

        Returns a string without "NULL" or unknown_date if there are other valid dates in
        event_dates. If there are no known dates in event_dates, the returned string will be the
        range of the min_date and max_date. If the min_date and max_date are the reserved start and
        end dates, the returned string will be the unknown date.

        Args:
            event_dates (set): Set of eventDate strings
            min_date (datetime.date): The earliest date represented by all the eventDates
            max_date (datetime.date): The latest date represented by all eventDates

        Returns:
            str: A fixed up version of the event_dates, joined by ' and ' if there are multiple
                dates.
        '''
        new_event_dates = ''
        non_null_event_dates = {x for x in event_dates if x not in ('NULL', self.unknown_date)}

        if non_null_event_dates:
            new_event_dates = ' and '.join(sorted(list(non_null_event_dates)))
        elif min_date == self.unknown_start_date and max_date == self.unknown_end_date:
            new_event_dates = self.unknown_date
        elif min_date.year == max_date.year:
            new_event_dates = str(min_date.year)
        else:
            new_event_dates = f'{min_date.year}-{max_date.year}'
        return new_event_dates


class DateHandler(ABC):
    @abstractmethod
    def handle(self, date: str):
        pass

    @abstractmethod
    def set_next(self, handler):
        pass


class BaseDateHandler(DateHandler):
    _next_handler = None

    def set_next(self, handler: DateHandler):
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, date: str):
        if self._next_handler:
            return self._next_handler.handle(date)
        raise UnknownDateFormat('Could not handle date "{}"'.format(date))


class UnknownDateHandler(BaseDateHandler):
    NO_DATE = re.compile(
        r'(?i)^$|^0\d{3}-\d{2}-\d{2}$|^9999.\d{2}.\d{2}$|^n\.?d\.?$|^NULL$|^\[?\d{2}[-_]*\??\]?$|'
        r'^\d$|^[A-Za-z\s]+$|^no\s+date$|^undated$|^n/a$|'
        r'unknown') # <- Special case: if unknown is anywhere in string, the date must be unknown

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        self.unknown_date = unknown_date
        self.unknown_start_date = unknown_start_date
        self.unknown_end_date = unknown_end_date

    def handle(self, date: str):
        if self.NO_DATE.match(date) is not None:
            return (self.unknown_date, [self.unknown_start_date, self.unknown_end_date])
        return super().handle(date)


class YearRangeHandler(BaseDateHandler):
    YEAR_RANGE = re.compile(
        r'(?i)^(?P<first_year>[1-2]\d{3})'
        r'\s*(?:-|and|to)\s*'
        r'(?P<second_year>(?:\d{2}|[1-2]\d{3}))$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        cleaned_date = date.replace('-00-00', '').replace(' ', '')
        match_obj = self.YEAR_RANGE.match(cleaned_date)
        if match_obj is None:
            return super().handle(date)

        first_year = match_obj.group('first_year')
        second_year = match_obj.group('second_year')
        if len(second_year) == 2:
            second_year = f'{first_year[0:2]}{second_year}'
        first_year_num = int(first_year)
        second_year_num = int(second_year)

        if second_year_num < first_year_num:
            # Swap
            first_year_num, second_year_num = second_year_num, first_year_num
            first_year, second_year = second_year, first_year

        event_date = first_year if first_year_num == second_year_num else f'{first_year} - {second_year}'
        early_date = datetime.date(first_year_num, 1, 1)
        late_date = datetime.date(second_year_num, 12, 31)
        return (event_date, [early_date, late_date])


class YearMonthDayHandler(BaseDateHandler):
    YYYY_MM_DD = re.compile(
        r'^(?P<year>[1-2]\d{3})'
        r'[-\./]?'
        r'(?P<month>1[0-2]|0?[1-9])'
        r'[-\./]?'
        r'(?P<date>3[0-1]|[1-2][0-9]|0?[1-9])$')

    MM_DD_YYYY = re.compile(
        r'^(?P<month>1[0-2]|0?[1-9])'
        r'[-\./]?'
        r'(?P<date>3[0-1]|[1-2][0-9]|0?[1-9])'
        r'[-\./]?'
        r'(?P<year>[1-2]\d{3})$')

    DD_MM_YYYY = re.compile(
        r'^(?P<date>3[0-1]|[1-2][0-9]|0?[1-9])'
        r'[-\./]?'
        r'(?P<month>1[0-2]|0?[1-9])'
        r'[-\./]?'
        r'(?P<year>[1-2]\d{3})$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        match_obj = None
        for regex in (self.YYYY_MM_DD, self.MM_DD_YYYY, self.DD_MM_YYYY):
            match_obj = regex.match(date)
            if match_obj is not None:
                break
        if match_obj is None:
            return super().handle(date)

        year = match_obj.group('year')
        month = match_obj.group('month')
        day = match_obj.group('date')
        year_num = int(year)
        month_num = int(month)
        day_num = int(day)

        days_in_month = monthrange(year_num, month_num)[1]
        if day_num > days_in_month:
            day_num = days_in_month

        event_date = f"{year}-{month.rjust(2, '0')}-{str(day_num).rjust(2, '0')}"
        exact_date = datetime.date(year_num, month_num, day_num)
        return (event_date, [exact_date])


class YearMonthRangeHandler(BaseDateHandler):
    YEAR_MONTH_RANGE = re.compile(
        r'^(?P<year_1>[1-2]\d{3})'
        r'[-\./]'
        r'(?P<month_1>1[0-2]|0?[1-9])'
        r'[-\./]'
        r'00'
        r'\s*-\s*'
        r'(?P<year_2>[1-2]\d{3})'
        r'[-\./]'
        r'(?P<month_2>1[0-2]|0?[1-9])'
        r'[-\./]'
        r'00$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        match_obj = self.YEAR_MONTH_RANGE.match(date)
        if match_obj is None:
            return super().handle(date)

        first_year = match_obj.group('year_1')
        first_month = match_obj.group('month_1')
        first_month_number = int(first_month)
        first_month_name = calendar.month_name[first_month_number]

        second_year = match_obj.group('year_2')
        second_month = match_obj.group('month_2')
        second_month_number = int(second_month)
        second_month_name = calendar.month_name[second_month_number]
        days_in_second_month = monthrange(int(second_year), second_month_number)[1]

        event_date = f'{first_month_name} {first_year} - {second_month_name} {second_year}'
        early_date = datetime.date(int(first_year), first_month_number, 1)
        late_date = datetime.date(int(second_year), second_month_number, days_in_second_month)
        return (event_date, [early_date, late_date])


class YearMonthDayRangeHandler(BaseDateHandler):
    YEAR_MONTH_DAY_RANGE = re.compile(
        r'^(?P<year_1>[1-2]\d{3})'
        r'[-\./]'
        r'(?P<month_1>1[0-2]|0?[1-9])'
        r'[-\./]'
        r'(?P<date_1>3[0-1]|[1-2][0-9]|0?[1-9])'
        r'\s*-\s*'
        r'(?P<year_2>[1-2]\d{3})'
        r'[-\./]'
        r'(?P<month_2>1[0-2]|0?[1-9])'
        r'[-\./]'
        r'(?P<date_2>3[0-1]|[1-2][0-9]|0?[1-9])$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        match_obj = self.YEAR_MONTH_DAY_RANGE.match(date)
        if match_obj is None:
            return super().handle(date)

        first_year = match_obj.group('year_1')
        first_month = match_obj.group('month_1')
        first_month_num = int(first_month)
        first_month_name = calendar.month_name[first_month_num]
        days_in_first_month = monthrange(int(first_year), first_month_num)[1]
        first_date_num = int(match_obj.group('date_1'))
        if first_date_num > days_in_first_month:
            first_date_num = days_in_first_month

        second_year = match_obj.group('year_2')
        second_month = match_obj.group('month_2')
        second_month_num = int(second_month)
        second_month_name = calendar.month_name[second_month_num]
        days_in_second_month = monthrange(int(second_year), second_month_num)[1]
        second_date_num = int(match_obj.group('date_2'))
        if second_date_num > days_in_second_month:
            second_date_num = days_in_second_month

        early_date = datetime.date(int(first_year), first_month_num, first_date_num)
        late_date = datetime.date(int(second_year), second_month_num, second_date_num)

        if early_date == late_date:
            first_month = str(first_month_num).rjust(2, '0')
            first_date = str(first_date_num).rjust(2, '0')
            event_date = f'{first_year}-{first_month}-{first_date}'
            date_range = [early_date]
        elif early_date < late_date:
            event_date = (f'{first_month_name} {first_date_num}, {first_year} - '
                          f'{second_month_name} {second_date_num}, {second_year}')
            date_range = [early_date, late_date]
        else:
            event_date = (f'{second_month_name} {second_date_num}, {second_year} - '
                          f'{first_month_name} {first_date_num}, {first_year}')
            date_range = [late_date, early_date]

        return (event_date, date_range)


class ZeroMonthHandler(BaseDateHandler):
    ZERO_MONTH = re.compile(
        r'^(?P<year>[1-2]\d{3})'
        r'[-\./]'
        r'(?P<month>00)'
        r'[-\./]'
        r'(?P<date>3[0-1]|[1-2][0-9]|0?[1-9])$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        match_obj = self.ZERO_MONTH.match(date)
        if match_obj is None:
            return super().handle(date)

        year = match_obj.group('year')
        year_num = int(year)
        early_date = datetime.date(year_num, 1, 1)
        late_date = datetime.date(year_num, 12, 31)
        return (year, [early_date, late_date])


class ZeroDayHandler(BaseDateHandler):
    ZERO_DAY = re.compile(
        r'^(?P<year>[1-2]\d{3})'
        r'[-\./]'
        r'(?P<month>1[0-2]|0?[1-9])'
        r'[-\./]'
        r'(?P<date>00)$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        match_obj = self.ZERO_DAY.match(date)
        if match_obj is None:
            return super().handle(date)

        year = int(match_obj.group('year'))
        month_number = int(match_obj.group('month'))
        days_in_month = monthrange(year, month_number)[1]
        month_name = calendar.month_name[month_number]

        early_date = datetime.date(year, month_number, 1)
        late_date = datetime.date(year, month_number, days_in_month)
        return (f'{month_name} {year}', [early_date, late_date])


class DecadeHandler(BaseDateHandler):
    DECADE = re.compile(
        r'(?i)^(?P<span>early|late)?\s*'
        r'(?P<decade>[1-2]\d{2})(-|_|0\'?s)$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def has_group(self, match, group):
        try:
            return bool(match.group(group))
        except IndexError:
            return False

    def handle(self, date: str):
        match_obj = self.DECADE.match(date)
        if match_obj is None:
            return super().handle(date)

        decade = match_obj.group('decade')
        span = match_obj.group('span').lower() if self.has_group(match_obj, 'span') else None

        if span is None:
            early_date = datetime.date(int(f'{decade}0'), 1, 1)
            late_date = datetime.date(int(f'{decade}9'), 12, 31)
        elif span == 'late':
            early_date = datetime.date(int(f'{decade}7'), 1, 1)
            late_date = datetime.date(int(f'{decade}9'), 12, 31)
        elif span == 'early':
            early_date = datetime.date(int(f'{decade}0'), 1, 1)
            late_date = datetime.date(int(f'{decade}3'), 12, 31)
        else:
            raise UnknownDateFormat('Could not handle decade date "{}"'.format(date))
        return (f'{decade}0s', [early_date, late_date])


class DecadeRangeHandler(BaseDateHandler):
    DECADE_RANGE = re.compile(
        r'(?i)^'
        r'(?P<decade_1>[1-2]\d{2})(-|_|0\'?s)'
        r'\s*[-—]+\s*'
        r'(?P<decade_2>[1-2]\d{2})(-|_|0\'?s)'
        r'$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        match_obj = self.DECADE_RANGE.match(date)
        if match_obj is None:
            return super().handle(date)

        decade_1 = match_obj.group('decade_1')
        decade_2 = match_obj.group('decade_2')

        if int(decade_1) > int(decade_2):
            decade_1, decade_2 = decade_2, decade_1

        early_date = datetime.date(int(f'{decade_1}0'), 1, 1)
        late_date = datetime.date(int(f'{decade_2}9'), 12, 31)
        return (f'{decade_1}0 - {decade_2}9', [early_date, late_date])


class YearHandler(BaseDateHandler):
    YYYY = re.compile(r'^(?P<year>[1-2]\d{3})(?:-00-00)?$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        match_obj = self.YYYY.match(date)
        if match_obj is None:
            return super().handle(date)

        year = match_obj.group('year')
        year_num = int(year)
        early_date = datetime.date(year_num, 1, 1)
        late_date = datetime.date(year_num, 12, 31)
        return (year, [early_date, late_date])


class SeasonHandler(BaseDateHandler):
    SEASON = re.compile(
        r'(?i)(?P<season>spring|easter|summer|fall|winter|christmas|late|year end|early)\s*'
        r'(?P<year>[1-2]\d{3})')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        match_obj = self.SEASON.match(date)
        if match_obj is None:
            return super().handle(date)

        season = match_obj.group('season').lower()
        year = int(match_obj.group('year'))

        if season == 'early':
            early_date = datetime.date(year, 1, 1)
            # The following handles leap years
            late_date = datetime.date(year, 2, monthrange(year, 2)[1])
        elif season == 'spring':
            early_date = datetime.date(year, 3, 1)
            late_date = datetime.date(year, 5, 31)
        elif season == 'easter':
            early_date = datetime.date(year, 4, 1)
            late_date = datetime.date(year, 4, 30)
        elif season == 'summer':
            early_date = datetime.date(year, 6, 1)
            late_date = datetime.date(year, 8, 31)
        elif season == 'fall':
            early_date = datetime.date(year, 9, 1)
            late_date = datetime.date(year, 11, 30)
        elif season == 'winter':
            early_date = datetime.date(year, 12, 1)
            # The following handles leap years
            next_year = year + 1
            days_in_month = monthrange(next_year, 2)[1]
            late_date = datetime.date(next_year, 2, days_in_month)
        elif season == 'christmas':
            early_date = datetime.date(year, 12, 20)
            late_date = datetime.date(year, 12, 31)
        elif season == 'late':
            early_date = datetime.date(year, 11, 1)
            late_date = datetime.date(year, 12, 31)
        elif season == 'year end':
            early_date = datetime.date(year, 12, 1)
            late_date = datetime.date(year, 12, 31)
        else:
            raise UnknownDateFormat('Could not handle seasonal date "{}"'.format(date))
        return (f'{season.capitalize()} {year}', [early_date, late_date])


class MonthWordYearHandler(BaseDateHandler):
    MONTH_WORD_YEAR = re.compile(
        r'(?i)^(?P<span>early|end of|late)?\s*'
        r'(?P<month_name>jan(?:\.?|uary)?|feb(?:\.?|ruary)?|mar(?:\.?|ch)?|apr(?:\.?|il)?|'
        r'may\.?|jun(?:\.?|e)?|jul(?:\.?|y)?|aug(?:\.?|ust)?|sep(?:\.?|t\.?|tember)?|'
        r'oct(?:\.?|ober)?|nov(?:\.?|ember)?|dec(?:\.?|ember)?)\s*'
        r'(?P<year>[1-2]\d{3})$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def has_group(self, match, group):
        try:
            return bool(match.group(group))
        except IndexError:
            return False

    def handle(self, date: str):
        match_obj = self.MONTH_WORD_YEAR.match(date)
        if match_obj is None:
            return super().handle(date)

        month_abbr = match_obj.group('month_name')[0:3]
        month_number = ABBREV_MONTH_WORDS.index(month_abbr.capitalize())
        month_name = calendar.month_name[month_number]
        year = int(match_obj.group('year'))
        days_in_month = monthrange(year, month_number)[1]

        span = match_obj.group('span').lower() if self.has_group(match_obj, 'span') else None

        if span is None:
            early_date = datetime.date(year, month_number, 1)
            late_date = datetime.date(year, month_number, days_in_month)
        elif span == 'early':
            early_date = datetime.date(year, month_number, 1)
            late_date = datetime.date(year, month_number, 10)
        elif span == 'end of':
            early_date = datetime.date(year, month_number, 16)
            late_date = datetime.date(year, month_number, days_in_month)
        elif span == 'late':
            early_date = datetime.date(year, month_number, 21)
            late_date = datetime.date(year, month_number, days_in_month)
        else:
            raise UnknownDateFormat('Could not handle month, year with span "{}"'.format(date))
        return (f'{month_name} {year}', [early_date, late_date])


class MonthWordDayYearHandler(BaseDateHandler):
    MONTH_WORD_DAY_YEAR = re.compile(
        r'(?i)^(?P<month_name>jan(?:\.?|uary)?|feb(?:\.?|ruary)?|mar(?:\.?|ch)?|apr(?:\.?|il)?|'
        r'may\.?|jun(?:\.?|e)?|jul(?:\.?|y)?|aug(?:\.?|ust)?|sep(?:\.?|t\.?|tember)?|'
        r'oct(?:\.?|ober)?|nov(?:\.?|ember)?|dec(?:\.?|ember)?)\s*'
        r'(?P<date>3[0-1]|[1-2][0-9]|0?[1-9])(?:,\s*|\s+)'
        r'(?P<year>[1-2]\d{3})$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        match_obj = self.MONTH_WORD_DAY_YEAR.match(date)
        if match_obj is None:
            return super().handle(date)

        month_abbr = match_obj.group('month_name')[0:3]
        month_number = ABBREV_MONTH_WORDS.index(month_abbr.capitalize())
        year = match_obj.group('year')
        date = match_obj.group('date')

        event_date = f'{year}-{str(month_number).rjust(2, "0")}-{date.rjust(2, "0")}'
        exact_date = datetime.date(int(year), month_number, int(date))
        return (event_date, [exact_date])


class DayMonthWordYearHandler(BaseDateHandler):
    DAY_MONTH_WORD_YEAR = re.compile(
        r'(?i)^(?P<date>3[0-1]|[1-2][0-9]|0?[1-9])-'
        r'(?P<month_name>jan(?:\.?|uary)?|feb(?:\.?|ruary)?|mar(?:\.?|ch)?|apr(?:\.?|il)?|'
        r'may\.?|jun(?:\.?|e)?|jul(?:\.?|y)?|aug(?:\.?|ust)?|sep(?:\.?|t\.?|tember)?|'
        r'oct(?:\.?|ober)?|nov(?:\.?|ember)?|dec(?:\.?|ember)?)-'
        r'(?P<year>[1-2]\d{2,4})$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        match_obj = self.DAY_MONTH_WORD_YEAR.match(date)
        if match_obj is None:
            return super().handle(date)

        month_abbr = match_obj.group('month_name')[0:3]
        month_number = ABBREV_MONTH_WORDS.index(month_abbr.capitalize())
        year = match_obj.group('year')
        if len(year) == 2:
            year = f'19{year}' # TODO: This is pretty naive, should be changed
        date = match_obj.group('date')

        event_date = f'{year}-{str(month_number).rjust(2, "0")}-{date.rjust(2, "0")}'
        exact_date = datetime.date(int(year), month_number, int(date))
        return (event_date, [exact_date])


class MonthWordDayYearRangeHandler(BaseDateHandler):
    MONTH_WORD_YEAR_RANGE = re.compile(
        r'(?i)^(?P<month_name_1>jan(?:\.?|uary)?|feb(?:\.?|ruary)?|mar(?:\.?|ch)?|apr(?:\.?|il)?|'
        r'may\.?|jun(?:\.?|e)?|jul(?:\.?|y)?|aug(?:\.?|ust)?|sep(?:\.?|t\.?|tember)?|'
        r'oct(?:\.?|ober)?|nov(?:\.?|ember)?|dec(?:\.?|ember)?)\s*'
        r'(?:(?P<date_1>3[0-1]|[1-2][0-9]|0?[1-9])(?:,\s*|,?\s+))?'
        r'(?P<year_1>[1-2]\d{3})'
        r'\s*(?:-|to)\s*'
        r'(?P<month_name_2>jan(?:\.?|uary)?|feb(?:\.?|ruary)?|mar(?:\.?|ch)?|apr(?:\.?|il)?|'
        r'may\.?|jun(?:\.?|e)?|jul(?:\.?|y)?|aug(?:\.?|ust)?|sep(?:\.?|t\.?|tember)?|'
        r'oct(?:\.?|ober)?|nov(?:\.?|ember)?|dec(?:\.?|ember)?)\s*'
        r'(?:(?P<date_2>3[0-1]|[1-2][0-9]|0?[1-9])(?:,\s*|,?\s+))?'
        r'(?P<year_2>[1-2]\d{3})$')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def has_group(self, match, group):
        try:
            return bool(match.group(group))
        except IndexError:
            return False

    def handle(self, date: str):
        match_obj = self.MONTH_WORD_YEAR_RANGE.match(date)
        if match_obj is None:
            return super().handle(date)

        month_1_abbr = match_obj.group('month_name_1')[0:3]
        month_1_num = ABBREV_MONTH_WORDS.index(month_1_abbr.capitalize())
        month_1_name = calendar.month_name[month_1_num]
        year_1_num = int(match_obj.group('year_1'))
        days_in_month_1 = monthrange(year_1_num, month_1_num)[1]

        if self.has_group(match_obj, 'date_1'):
            day_1_num = int(match_obj.group('date_1')) or 1
            if day_1_num > days_in_month_1:
                day_1_num = days_in_month_1
        else:
            day_1_num = 1

        month_2_abbr = match_obj.group('month_name_2')[0:3]
        month_2_num = ABBREV_MONTH_WORDS.index(month_2_abbr.capitalize())
        month_2_name = calendar.month_name[month_2_num]
        year_2_num = int(match_obj.group('year_2'))
        days_in_month_2 = monthrange(year_2_num, month_2_num)[1]

        if self.has_group(match_obj, 'date_2'):
            day_2_num = int(match_obj.group('date_2')) or 1
            if day_2_num > days_in_month_2:
                day_2_num = days_in_month_2
        else:
            day_2_num = days_in_month_2

        early_date = datetime.date(year_1_num, month_1_num, day_1_num)
        late_date = datetime.date(year_2_num, month_2_num, day_2_num)

        if early_date > late_date:
            year_1_num, year_2_num = year_2_num, year_1_num
            month_1_name, month_2_name = month_2_name, month_1_name
            month_1_num, month_2_num = month_2_num, month_1_num
            day_1_num, day_2_num = day_2_num, day_1_num
            early_date, late_date = late_date, early_date

        if early_date == late_date:
            month_str = str(month_1_num).rjust(2, '0')
            day_str = str(day_1_num).rjust(2, '0')
            event_date = f'{year_1_num}-{month_str}-{day_str}'
        else:
            event_date = (f'{month_1_name} {day_1_num}, {year_1_num}'
                          ' - '
                          f'{month_2_name} {day_2_num}, {year_2_num}')

        return (event_date, [early_date, late_date])


class DateParserHandler(BaseDateHandler):
    LANGUAGES = ['en', 'fr']
    DATEPARSER_SETTINGS = {
        'PREFER_DAY_OF_MONTH': 'first',
        'PREFER_DATES_FROM': 'past',
    }

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        pass

    def handle(self, date: str):
        ''' dateparser.parse is slow when the date is in an unrecognizable format. This should be
        avoided at all costs to avoid a performance hit.
        '''
        parsed_date = dateparser.parse(date, languages=self.LANGUAGES,
                                       settings=self.DATEPARSER_SETTINGS)
        if parsed_date is None or parsed_date.year > datetime.datetime.now().year:
            return super().handle(date)
        date_ = parsed_date.date()
        return (date_.strftime(r'%Y-%m-%d'), [date_])


class YearAnywhereInDateHandler(BaseDateHandler):
    YYYY_NO_ANCHORS = re.compile(r'(?P<year>[1-2]\d{3})')

    def __init__(self, unknown_date, unknown_start_date, unknown_end_date):
        self.earliest_year = unknown_start_date.year

    def handle(self, date: str):
        ''' If literally nothing else worked, we can try to search for a year anywhere in the string.
        This is not ideal since there may be some day/month data being left behind...
        '''
        match_obj = self.YYYY_NO_ANCHORS.search(date)
        if match_obj is None:
            return super().handle(date)

        year = match_obj.group('year')
        year_num = int(year)

        if year_num > datetime.datetime.now().year:
            return super().handle(date)
        if year_num < self.earliest_year:
            return super().handle(date)

        early_date = datetime.date(year_num, 1, 1)
        late_date = datetime.date(year_num, 12, 31)
        return (year, [early_date, late_date])
