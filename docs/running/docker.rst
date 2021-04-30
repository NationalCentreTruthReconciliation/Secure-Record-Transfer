Running with Docker Compose
===========================

The easiest way to run the application is to run the entire thing with Docker. This is the preferred
method to run the app if you aren't doing any sort of development on the app. If you do want to work
on the Django app's backend, refer to the section on :ref:`Running Locally for Development`.

First, make sure you've installed Docker. Create an environment file called :code:`.dockerenv` in
the :code:`bagitobjecttransfer` folder. Put these contents in it if it's not already created:

::

    BAG_STORAGE_FOLDER = /app/media/bags
    ARCHIVIST_EMAIL=<your email address>

    MYSQL_ROOT_PASSWORD=root-pw
    MYSQL_DATABASE=records-transfer-db
    MYSQL_USER=records-user
    MYSQL_PASSWORD=records-password


.. note::

    The first time the MySQL container is created, the MYSQL_USER and MYSQL_PASSWORD settings are
    used to create a super-user account with all privileges on the database. The MYSQL_ROOT_PASSWORD
    setting is also used to create a password for the root super-user account used to access the
    database.


After ensuring you have a minimal environment file set up, make sure you are in the
:code:`bagitobjecttransfer` folder, and run all of the services with Docker:

.. code-block:: console

    $ docker-compose up -d


If this is your first time running the app in this configuration, you will first want to do a few
things. These are:

1. Update permissions on :code:`mysqld.cnf`
2. Migrate the database tables
3. Create a super user


Update MySQL Configuration Permissions
######################################

If you run the :code:`docker-compose up` command and receive a warning from the database container
like :code:`mysqld: [Warning] World-writable config file '/etc/mysql/mysqld.cnf' is ignored.`, you
need to update the file's permissions so it is not world-writable. This configuration file tells
MySQL where to store logs, so if it is not used, the log files will be more difficult to find.

To update the permissions, run these commands:

.. code-block:: console

    (env) $ docker-compose exec db sh
    # chmod 755 /etc/mysql/mysqld.cnf
    # exit
    (env) $


And then you can restart the app:

.. code-block:: console

    (env) $ docker-compose down
    (env) $ docker-compose up -d


Migrating the Database Tables and Creating a Super-User
#######################################################

Migrating the database tables and creating a super user are both tasks that are run in the Django
:code:`app` container, and so can be run one after another. To complete these tasks, run:

.. code-block:: console

    (env) $ docker-compose exec app sh
    # python3 manage.py migrate
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
