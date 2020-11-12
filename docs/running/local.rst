Running Locally for Development
===============================

Running locally is best accomplished using a mixture of running services in Docker containers and
directly on your machine. If you are on Windows, you will want to run everything from within WSL.
The following table outlines the simplest way to start the services to be run for development
purposes.

+-----------+-----------------+---------------+-----------------------------------+
|**Service**|**Run on Docker**|**Run Locally**|**Notes**                          |
+-----------+-----------------+---------------+-----------------------------------+
|Database   |                 |YES            |SQLite3 database is used, not MySQL|
+-----------+-----------------+---------------+-----------------------------------+
|Django App |                 |YES            |Running locally is easier to debug |
+-----------+-----------------+---------------+-----------------------------------+
|Email      |YES              |               |Uses MailHog                       |
+-----------+-----------------+---------------+-----------------------------------+
|Redis      |YES              |               |                                   |
+-----------+-----------------+---------------+-----------------------------------+
|RQ Workers |YES              |               |                                   |
+-----------+-----------------+---------------+-----------------------------------+

First, make sure you've installed Docker. Create an environment file called :code:`.dockerenv` in
the :code:`bagitobjecttransfer` folder. Put these contents in it if it's not already created:

.. code-block::

    BAG_FOLDER_LINUX = /app/media/bags


Create a virtual environment to run the app out of if you haven't already. :code:`cd` to the root of
the repository (the same directory as the :code:`README.md` file), create a new environment, and
install the required packages:

.. code-block::

    $ python -m venv env/
    $ source env/bin/activate
    $ python -m pip install -r bagitobjecttransfer/requirements.txt


To run the app, you will want to start the Redis and Email services before you start the development
web server, since the Django app depends on those. There is a docker-compose file created
specifically for this purpose. First, :code:`cd` into the code:`bagitobjecttransfer` folder, then
run the docker-compose command:

.. code-block::

    $ cd bagitobjecttransfer
    $ docker-compose -f docker-compose.dev.yml up -d


.. note::

    Note that the docker-compose command runs the services in *detached* mode. To see the output
    logs from the rq worker service, open Docker Desktop on your computer or run
    :code:`docker logs recordtransfer_rq_workers_dev`


Once the Docker services are running, spinning up the app and the database can both be completed
using one command. If this is your first time running the app, you will first want to populate the
database tables and create a super user before running the development server. To do so, execute
the following two commands, and follow the prompts:

.. code-block::

    $ python3 manage.py migrate
    $ python3 manage.py createsuperuser


.. note::

    Always make sure your virtual environment is activated when you use the :code:`python3` command
    in the repository!


Once your database has been created and a super user exists, run the development server with this
command:

.. code-block:: console

    $ python3 manage.py runserver


You should now be able to access the app at http://127.0.0.1:8000 or http://localhost:8000 in your
favourite browser.

Any emails that the app sends are intercepted by the MailHog server. You can see the emails by
visiting http://localhost:8025 in your favourite browser.
