Running with Docker Compose
===========================

Using Docker is the simplest way to test the record transfer application out on your local computer.
Docker is not recommended for deploying the app, to do so, follow the instructions for
:ref:`Deploying in Production`.

To run the app in Docker, first make sure you've installed Docker. You can go to the
`Docker website <https://docs.docker.com/get-docker/>`_ to find download links for your operating
system. Note that in Windows, you'll also need to
`install WSL <https://docs.microsoft.com/en-us/windows/wsl/install-win10>`_. Once Docker is
installed, clone or download the code from the
`GitHub repository <https://github.com/danloveg/NCTR-Bagit-Record-Transfer>`_.

From the root of the repository, go to the :code:`bagitobjecttransfer` folder. This is the same
folder where you will find a file called :code:`manage.py`. Once in the folder, create a
file called :code:`.dockerenv`, and put these contents in it:

::

    BAG_STORAGE_FOLDER = /app/media/bags
    ARCHIVIST_EMAIL=<your email address>

    MYSQL_ROOT_PASSWORD=root-pw
    MYSQL_DATABASE=records-transfer-db
    MYSQL_USER=records-user
    MYSQL_PASSWORD=records-password


This is an environment variable file, which is used to control some parts of the application.

.. note::

    The first time the MySQL container is created, the MYSQL_USER and MYSQL_PASSWORD settings are
    used to create a super-user account with all privileges on the database. The MYSQL_ROOT_PASSWORD
    setting is also used to create a password for the root super-user account used to access the
    database.


After ensuring you have a minimal environment file set up, you can start up the application in
Docker with this command:

.. code-block:: console

    $ docker-compose up -d


The app will appear in Docker Desktop provided Docker is installed. To stop the app, you may click
the Stop button in Docker Desktop, or run this command:

.. code-block:: console

    $ docker-compose down


If this is your first time running the app in this configuration, you will first want to create a
super user so that you can log in to the application.

Creating a Super-User
#####################

Creating a super user is a task that should be run in the Django :code:`app` container. To create
a new super user, run these commands and follow the user creation prompts (you will be asked for
your name, email, etc.):

.. code-block:: console

    (env) $ docker-compose exec app sh
    # python3 manage.py createsuperuser
    # exit
    (env) $


Using the App
#############

After completing the setup and starting the services with Docker, you should be able to access the
app at http://127.0.0.1:8000 or http://localhost:8000 in your browser. If you created a super user,
you will be able to log in to the application with that super user account. New users can be added
from the admin backend (https://localhost:8000/admin/recordtransfer/user/) or by using the sign-up
page.

Using the sign up page requires you to verify the new account by email. Any emails that the app
sends are intercepted by the MailHog server. You can see the emails by visiting
http://localhost:8025 in your browser.

.. note::

    The logs are disabled for the mail server since they are too verbose. To re-enable them, remove
    the :code:`logging` section for the email service in the :code:`docker-compose.yml` file.


The log files for all of the containers go to :code:`bagitobjecttransfer/docker/logs/`.
