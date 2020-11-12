Production Build
================

WORK IN PROGRESS!

.. code-block::

    # Secret settings that should not be committed or otherwise publically available
    SECRET_KEY=
    RQ_HOST=
    RQ_PORT=
    RQ_PASSWORD=
    RQ_DB=
    EMAIL_HOST=
    EMAIL_PORT=
    EMAIL_HOST_USER=
    EMAIL_HOST_PASSWORD=

To get a new secret key, run the following command:

.. code-block:: console

    $ python3 -c "from django.core.management.utils import get_random_secret_key as gsk; print(gsk())"
