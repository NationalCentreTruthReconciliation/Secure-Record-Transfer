Running the App
===============

The following two sections indicate how you can get the app up and running in either a
Development/Debug environment, or in a Production environment. Running the production app can get
very involved, so be prepared to read.

*******************
Development (Local)
*******************

To run the app locally, we can use the development server bundled with Django. But first, we have to
start up Redis locally and create a Redis worker. To start up Redis:

.. code-block:: console

    $ redis-server redis.conf &

If you do not have a redis configuration file, you can visit this link to download a sample config:
https://download.redis.io/redis-stable/redis.conf.

To stop the server at any point, use the :code:`jobs` command to find the ID of the Redis job. If
for example the ID is 1, run this command to stop the server:

.. code-block:: console

    $ kill %1

Once Redis is running, we can create a worker that will attach to that Redis server. From the top of
the repository, :code:`cd` into the bagitobjecttransfer folder:

.. code-block:: console

    $ cd bagitobjecttransfer

Then, use the manage script to create one worker:

.. code-block:: console

    $ python3 manage.py rqworker default &

To stop the worker at any point, use the method above with the :code:`jobs` command.

Set environment SECRET_KEY:

.. code-block:: console

    $ SECRET=$(python3 -c "from django.management.utils import get_random_secret_key as gsk; print(gsk());")
    $ echo -e "SECRET_KEY=${SECRET}\n" > .env


**********
Production
**********

Under construction

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
