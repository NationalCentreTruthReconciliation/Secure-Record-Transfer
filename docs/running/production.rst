Deploying in Production
=======================

The setup for a production build is much more involved than the development and Docker methods.

To manage services, systemd is used. The OS used for this guide is Red Hat Enterprise Linux 7. There
may be some differences if you intend to deploy the app on a different Linux distribution, but the
basics should be the same.

Transfer App Code
#################

.. note::

    We are using Python version **3.6.8**. You can
    `download Python 3.6.8 here <https://www.python.org/downloads/release/python-368/>`_.


If you have not already done so, clone the application, and move the repo into the :code:`/opt/`
directory.

.. code-block:: console

    $ cd ~
    $ git clone https://github.com/danloveg/NCTR-Bagit-Record-Transfer.git
    $ sudo mv NCTR-Bagit-Record-Transfer /opt/


Create a virtual environment to install dependencies and to run the app from.

.. code-block:: console

    $ cd /opt/NCTR-Bagit-Record-Transfer
    $ python3 -m venv env/


Install Django and all other dependencies in the virtual environment.

.. code-block:: console

    $ source env/bin/activate
    $ cd bagitobjecttransfer
    $ pip install -r requirements.txt


Redis and RQ Worker Setup
#########################

.. note::

    We are using Redis version **3.2.12**. You can
    `download Redis 3.2.12 here <http://download.redis.io/releases/redis-3.2.12.tar.gz>`_.


Create a systemd service initialization file for redis if it doesn't exist at
:code:`/usr/lib/systemd/system/redis.service`

.. code-block::

    # file /usr/lib/systemd/system/redis.service
    [Unit]
    Description=Redis persistent key-value database
    After=network.target
    After=network-online.target
    Wants=network-online.target

    [Service]
    ExecStart=/usr/bin/redis-server /etc/redis.conf --supervised systemd
    ExecStop=/usr/libexec/redis-shutdown
    Type=notify
    User=redis
    Group=redis
    RuntimeDirectory=redis
    RuntimeDirectoryMode=0755

    [Install]
    WantedBy=multi-user.target


This script tells redis that the configuration file is at :code:`/etc/redis.conf`. If you do not
have a redis configuration file already, you can get one
`here <https://raw.githubusercontent.com/redis/redis/3.0/redis.conf>`_ and copy it to
:code:`/etc/redis.conf`. You will want to edit a few of the default settings, to do so, search in
the :code:`redis.conf` file and change these settings:

.. code-block::

    # file /etc/redis.conf
    databases 1
    logfile /var/log/redis/redis.log
    dir /var/lib/redis/
    supervised systemd


You should now be able to start and restart the redis service with the following command:

.. code-block:: console

    $ sudo service redis start
    $ sudo service redis restart


To set up the asynchronous RQ workers, create a new environment file at
:code:`/opt/NCTR-Bagit-Record-Transfer/.env` if it doesn't exist already. This file is used to store
all of the secrets used for the record transfer application.

Add these lines to the environment file:

.. code-block::

    # file /opt/NCTR-Bagit-Record-Transfer/.env
    RQ_HOST_DEFAULT=localhost
    RQ_PORT_DEFAULT=6379
    RQ_DB_DEFAULT=0
    RQ_PASSWORD_DEFAULT=
    RQ_TIMEOUT_DEFAULT=500


This is all that the RQ workers need to function correctly.


MySQL Setup
###########

.. note::

    We are using MySQL Community Server version **8.0.22**. Download
    `MySQL Community Server here <https://dev.mysql.com/downloads/mysql/>`_.


Create a systemd service initialization file for MySQL if it doesn't exist at
:code:`/usr/lib/systemd/system/mysqld.service`

.. code-block::

    # file /usr/lib/systemd/system/mysqld.service
    [Unit]
    Description=MySQL Server
    Documentation=man:mysqld(8)
    Documentation=http://dev.mysql.com/doc/refman/en/using-systemd.html
    After=network.target
    After=syslog.target

    [Install]
    WantedBy=multi-user.target

    [Service]
    User=mysql
    Group=mysql
    Type=notify
    TimeoutSec=0 # Disable service start and stop timeout logic of systemd for mysqld service.
    PermissionsStartOnly=true # Execute pre and post scripts as root
    ExecStartPre=/usr/bin/mysqld_pre_systemd # Needed to create system tables
    ExecStart=/usr/sbin/mysqld $MYSQLD_OPTS # Start main service
    EnvironmentFile=-/etc/sysconfig/mysql # Use this to switch malloc implementation
    LimitNOFILE = 10000 # Sets open_files_limit
    Restart=on-failure
    RestartPreventExitStatus=1
    PrivateTmp=false
    # Set enviroment variable MYSQLD_PARENT_PID. This is required for restart.
    Environment=MYSQLD_PARENT_PID=1


You should now be able to start and restart the MySQL service with the following commands:

.. code-block:: console

    $ sudo service mysqld start
    $ sudo service mysqld restart


Once the MySQL server has started up, we will need to log in to MySQL and do two things:

1. Create an empty database
2. Create a user for the database


*********************
Create Empty Database
*********************

To create an empty database, log in to the running MySQL server:

.. code-block:: console

    $ sudo mysql -u root


When you're logged in, check to make sure the database has not already been created. Execute a
SHOW query to see all the databases. You'll see something like the below output if the database
hasn't been created already. If you see a database named :code:`recordtransfer`, the database
already exists.

.. code-block::

    mysql> SHOW DATABASES;
    +--------------------+
    | Database           |
    +--------------------+
    | information_schema |
    | mysql              |
    | performance_schema |
    | sys                |
    +--------------------+
    4 rows in set (0.00 sec)


Create the **recordtransfer** database if it hasn't been created already:

.. code-block::

    mysql> CREATE DATABASE recordtransfer;
    Query OK, 1 row affected (0.00 sec)


********************
Create Database User
********************

Now that the database exists, we will create a new account for this database that the record
transfer app will use to interact with the database. We will call the user **django**. Remember the
password you use, you will need to enter it one more place later.

.. code-block::

    mysql> CREATE USER 'django'@'%' IDENTIFIED WITH mysql_native_password BY 'password';
    Query OK, 0 rows affected (0.00 sec)

    mysql> GRANT ALL ON recordtransfer.* TO 'django'@'%';
    Query OK, 0 rows affected (0.00 sec)

    mysql> FLUSH PRIVILEGES;
    Query OK, 0 rows affected (0.00 sec)

    mysql> EXIT;
    Bye


.. note::

    If you get an error when creating the password that it doesn't meet the policy requirements, you
    can check the requirements by running the MySQL query:

    .. code-block::

        SHOW VARIABLES LIKE 'validate_password%';


    You can find more info on `MySQL password validation here
    <https://dev.mysql.com/doc/refman/8.0/en/validate-password-options-variables.html>`_.


***********************************
Add MySQL Connection to Environment
***********************************

To tell the record transfer app to use the **recordtransfer** MySQL database as the **django** user,
edit the environment file at :code:`/opt/NCTR-Bagit-Record-Transfer/.env`. Remember, this file is
used to store all of the secrets used for the record transfer application.

Add these lines to the environment file, substituting 'password' for the password you used above:

.. code-block::

    # file /opt/NCTR-Bagit-Record-Transfer/.env
    MYSQL_HOST=localhost
    MYSQL_DATABASE=recordtransfer
    MYSQL_USER=django
    MYSQL_PASSWORD='password'


Environment Setup
#################

So far, your environment file :code:`/opt/NCTR-Bagit-Record-Transfer/.env` should look something
like this:

.. code-block::

    # file /opt/NCTR-Bagit-Record-Transfer/.env
    MYSQL_HOST=localhost
    MYSQL_DATABASE=recordtransfer
    MYSQL_USER=django
    MYSQL_PASSWORD='password'

    RQ_HOST=localhost
    RQ_PORT=6379
    RQ_PASSWORD=
    RQ_DB=0

    EMAIL_HOST=
    EMAIL_PORT=
    EMAIL_HOST_USER=
    EMAIL_HOST_PASSWORD=

To get a new secret key, run the following command:

.. code-block:: console

    $ python3 -c "from django.core.management.utils import get_random_secret_key as gsk; print(gsk())"

