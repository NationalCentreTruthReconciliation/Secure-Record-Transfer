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
the :code:`bagitobjecttransfer` folder. Put these contents in it if it's not already created (the
first line is a comment, you do not need to put that line in):

::

    # file bagitobjecttransfer/.dockerenv
    BAG_STORAGE_FOLDER=/app/media/bags
    ARCHIVIST_EMAIL=<some email address>


Through a quirk of running some services in docker and some not, you also need to create an
environment file called :code:`.env` in the :code:`bagitobjecttransfer` folder that agrees with the
:code:`.dockerenv` file. The main difference is that the BAG_STORAGE_FOLDER will need to be an
absolute path **on your computer** to a media folder in your repository. This is an example:

::

    # file bagitobjecttransfer/.env
    BAG_STORAGE_FOLDER=/home/user/repos/NCTR-Bagit-Record-Transfer/bagitobjecttransfer/media/bags
    ARCHIVIST_EMAIL=<the same email address>


The directory :code:`/home/user/repos/NCTR-Bagit-Record-Transfer` will depend entirely on where you
cloned the repository to on your computer. The rest of the path will be the same regardless of where
the repo is.

.. note::

    A note for Windows users: The BAG_STORAGE_FOLDER must be a WSL path, as you will need to run the
    Django server from WSL. If your BAG_STORAGE_FOLDER starts with a drive letter like C: or has
    backslashes instead of forward slashes, you know your path is incorrect.


Once you've created the required environment variable files, create a virtual environment to run the
app out of if you haven't already. :code:`cd` to the root of the repository (the same directory as
the :code:`README.md` file), create a new environment, and install the required packages:

.. code-block:: console

    $ python3 -m venv env/
    $ source env/bin/activate
    (env) $ python3 -m pip install -r bagitobjecttransfer/requirements.txt


If this is your first time running the app, you will want to migrate the database tables and create
a super user account to use to log in to the app. To do so, run these commands:

.. code-block:: console

    (env) $ cd bagitobjecttransfer
    (env) $ python3 manage.py migrate
    (env) $ python3 manage.py createsuperuser


The :code:`createsuperuser` command will prompt you for your name and password. Remember the
username and password you enter as you will need these to log in to the app.

.. note::

    Always make sure your virtual environment is activated when you use the :code:`python3` command
    in the repository!


To run the app, you will want to start the Redis and Email services before you start the development
web server, since the Django app depends on those. There is a docker-compose file created
specifically for this purpose. :code:`cd` into the :code:`bagitobjecttransfer` folder, then run the
docker-compose command with the development compose file:

.. code-block:: console

    (env) $ cd bagitobjecttransfer
    (env) $ docker-compose -f docker-compose.dev.yml up -d


Once your database has been created, a super user exists, and the docker services are running, run
the development server with this command:

.. code-block:: console

    (env) $ python3 manage.py runserver


.. note::

    A note for Windows users: do not be tempted to run the server from Windows directly. **You MUST
    run the server within WSL**, or else you will run into a myriad of issues, and bags will get
    lost.


After completing the setup and starting all of the services, you should be able to access the app
at http://127.0.0.1:8000 or http://localhost:8000 in your browser. If you created a super user, you
will be able to log in to the application with that super user account. New users can be added
from the admin backend (https://localhost:8000/admin/recordtransfer/user/) or by using the sign-up
page.

Using the sign up page requires you to verify the new account by email. Any emails that the app
sends are intercepted by the MailHog server. You can see the emails by visiting
http://localhost:8025 in your browser.

.. note::

    The logs are disabled for the mail server since they are too verbose. To re-enable them, remove
    the :code:`logging` section for the email service in the :code:`docker-compose.yml` file.


The log files for all of the containers are written to :code:`bagitobjecttransfer/docker/logs/`.
