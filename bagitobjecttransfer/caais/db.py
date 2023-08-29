from django.db import connection
from django.db.models import CharField, Aggregate


MULTI_VALUE_SEPARATOR = '|'

# MySQL and SQLite have slightly different syntax for GROUP_CONCAT
if connection.vendor == 'sqlite':
    SEPARATOR_TEMPLATE = ', "{separator}"'
elif connection.vendor == 'mysql':
    SEPARATOR_TEMPLATE = ' SEPARATOR "{separator}"'
else:
    raise ValueError(f'The database type "{connection.vendor}" is not supported!')


class GroupConcat(Aggregate):
    ''' Aggregate multiple values be concatenating them into one string using a
    separator character. Similar to the join() function in Python.
    '''

    function = 'GROUP_CONCAT'
    template = '%(function)s(%(expressions)s%(separator)s)'

    def __init__(self, expression, separator=',', **extra):
        super(GroupConcat, self).__init__(
            expression,
            separator=SEPARATOR_TEMPLATE.format(separator=separator),
            output_field=CharField(),
            **extra
        )


class DefaultConcat(GroupConcat):
    ''' Aggregate values by concatenating them into one string using the
    MULTI_VALUE_SEPARATOR character as a separator.
    '''

    def __init__(self, expression, **extra):
        super().__init__(expression, separator=MULTI_VALUE_SEPARATOR, **extra)
