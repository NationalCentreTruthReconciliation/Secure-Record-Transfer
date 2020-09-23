Running the App
===============

The following two sections indicate how you can get the app up and running in either a
Development/Debug environment, or in a Production environment. Running the production app can get
very involved, so be prepared to read.

In both cases, ensure you have followed the prerequisites section to make sure everything is
installed and that you have a virtual Python environment ready to go.

*******************
Development (Local)
*******************

To run the app locally, we can use the development server bundled with Django, but there is a small
amount of setup to do first.

First, :code:`cd` to the app directory. You should be in the same directory as the :code:`README.md`
file. Then, :code:`cd` into the :code:`bagitobjecttransfer` folder. Create a new SQLite database
using the manage script. Then create a new superuser, following the prompts. Make sure you remember
the username and password you use.

.. code-block:: console

    $ python3 manage.py migrate
    $ python3 manage.py createsuperuser

Now that's set up, you can spin up Redis. To do so, change to whichever directory contains your
Redis configuration file, and run:

.. code-block:: console

    $ redis-server redis.conf &

If you do not have a redis configuration file, you can visit this link to download a sample config:
https://download.redis.io/redis-stable/redis.conf.

To stop the server at any point, use the :code:`jobs` command to find the ID of the Redis job. If
for example the ID is 1, run this command to stop the server:

.. code-block:: console

    $ kill %1

Once Redis is running, we can create a worker that will attach to that Redis server. :code:`cd` back
into the :code:`bagitobjecttransfer` folder and use the manage script to create one worker:

.. code-block:: console

    $ python3 manage.py rqworker default &

To stop the worker at any point, use the method above with the :code:`jobs` command. Once the worker
is started up and running in the background, you can feel free to run the development server:

.. code-block:: console

    $ python3 manage.py runserver

You should now be able to access the app at http://127.0.0.1:8000 or https://localhost:8000 in your
favourite browser.

**********
Production
**********

TBD.

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

.. code-block::

    python3 -c "from django.core.management.utils import get_random_secret_key as gsk; print(gsk())"
