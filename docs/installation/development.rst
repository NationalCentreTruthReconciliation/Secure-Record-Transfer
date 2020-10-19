Running Locally
===============

To run the app locally, we can use the development server bundled with Django, but there is a small
amount of setup to do first.

First, :code:`cd` to the app directory. You should be in the same directory as the :code:`README.md`
file. Then, :code:`cd` into the :code:`bagitobjecttransfer` folder. Create a new SQLite database
using the manage script:

.. code-block:: console

    $ python3 manage.py migrate

Next, create a new superuser, following the prompts:

.. code-block:: console

    $ python3 manage.py createsuperuser

Make sure you remember the username and password you use since that will be the account you'll use
to log in to the app.

Now that the application is set up, you can spin up Redis. To do so, change to whichever directory
contains your Redis configuration file, and run:

.. code-block:: console

    $ redis-server redis.conf &

If you do not have a redis configuration file, you can visit `this link
<https://download.redis.io/redis-stable/redis.conf>`_ to download a sample config.

To stop the server at any point, use the :code:`jobs` command to find the ID of the Redis job. If
for example the ID is 1, run this command to stop the server:

.. code-block:: console

    $ kill %1

Once Redis is running, we can create a worker that will attach to that Redis server. :code:`cd` back
into the :code:`bagitobjecttransfer` folder and use the manage script to create one worker:

.. code-block:: console

    $ python3 manage.py rqworker default &

To stop the worker at any point, use the method above with the :code:`jobs` command. Once the worker
is started up and running in the background, you can now run the development server:

.. code-block:: console

    $ python3 manage.py runserver

You should now be able to access the app at http://127.0.0.1:8000 or https://localhost:8000 in your
favourite browser.
