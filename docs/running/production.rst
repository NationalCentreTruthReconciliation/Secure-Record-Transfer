Deploying in Production
=======================

The setup for a production build is much more involved than the development and Docker methods.

To manage services, systemd is used. The OS used for this guide is Red Hat Enterprise Linux 7. There
may be some differences if you intend to deploy the app on a different Linux distribution, but the
basics should be the same.

At the end of the process, the most important files will be placed at the following locations in the
file system:

::

    /
    |_ etc/
        |_ nginx/
            |_ sites-available/
                |_ recordtransfer.conf
            |_ sites-enabled/
                |_ recordtransfer.conf -> /etc/nginx/sites-available/recordtransfer.conf
    |_ opt/
        |_ NCTR-Bagit-Record-Transfer/
            |_ gunicorn.sock        (Gunicorn UNIX socket)
            |_ bagitobjecttransfer/ (Django App)
            |_ .env                 (App Environment Variables)
    |_ srv/
        |_ www/
            |_ recordtransfer_bags/ (Where BagIt bags are stored)
    |_ usr/
        |_ lib/
            |_ systemd/
                |_ system/
                    |_ gunicorn.service
                    |_ mysqld.service
                    |_ nginx.service
                    |_ redis.service
                    |_ rqworker_default.service


1. Clone Record Transfer App
############################

.. note::

    We are using Python version **3.6.8**. You can
    `download Python 3.6.8 here <https://www.python.org/downloads/release/python-368/>`_.


If you have not already done so, clone the application. Once it's cloned, move the repo into the
:code:`/opt/` directory. We will be using the :code:`/opt/` folder to serve the application from.

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


Set up a location to store BagIt bags inside:

.. code-block:: console

    $ sudo mkdir -p /srv/www/recordtransfer_bags


.. note::

    You do not have to use the :code:`/srv/www/recordtransfer_bags/` directory, you can use any
    directory you like to store BagIt bags in.


Create an environment variable file for the application at
:code:`/opt/NCTR-Bagit-Record-Transfer/.env` if it doesn't exist already:

.. code-block:: console

    (env) $ touch /opt/NCTR-Bagit-Record-Transfer/.env


We will be editing this file throughout this guide. For right now, we only need to add two lines,
one giving the app the location of the bag storage folder, and the other specifying the settings
module to use:

::

    # file /opt/NCTR-Bagit-Record-Transfer/.env
    DJANGO_SETTINGS_MODULE=bagitobjecttransfer.settings.production
    BAG_STORAGE_FOLDER=/srv/www/recordtransfer_bags/


2. NGINX Setup
##############

.. note::

    We are using NGINX version **1.18.0**. You can
    `download NGINX 1.18.0 here <https://nginx.org/en/download/nginx-1.18.0.tar.gz>`_.


`NGINX <https://www.nginx.com/resources/wiki/>`_ is a high performance HTTP server and reverse
proxy. NGINX is used as both an HTTP server and a reverse proxy for the record transfer application.
It is used as an HTTP server for serving static content, and acts as a reverse proxy when requests
are sent to Gunicorn to interpret.

To serve the files from the application folder, NGINX needs the proper permissions to access the
files in the folder. Recursively set the owner and the group of every folder and file in the
application folder to **nginx**:

.. code-block:: console

    (env) $ sudo chown -R nginx:nginx /opt/NCTR-Bagit-Record-Transfer/


If the systemd initialization script for nginx doesn't exist, create one at
:code:`/usr/lib/systemd/system/nginx.service` and add these contents:

::

    # file /usr/lib/systemd/system/nginx.service
    [Unit]
    Description=nginx - high performance web server
    Documentation=http://nginx.org/en/docs/
    After=network-online.target remote-fs.target nss-lookup.target
    Wants=network-online.target

    [Service]
    Type=forking
    PIDFile=/var/run/nginx.pid
    ExecStart=/usr/sbin/nginx -c /etc/nginx/nginx.conf
    ExecReload=/bin/sh -c "/bin/kill -s HUP $(/bin/cat /var/run/nginx.pid)"
    ExecStop=/bin/sh -c "/bin/kill -s TERM $(/bin/cat /var/run/nginx.pid)"
    ExecStartPost = /bin/sleep 0.1

    [Install]
    WantedBy=multi-user.target


Enable the nginx service to start on system startup:

.. code-block:: console

    (env) $ sudo systemctl enable nginx


NGINX requires a configuration file to determine how to serve the record transfer application, so
create a new file at :code:`/etc/nginx/sites-available/recordtransfer.conf` and add these contents
to it, substituting :code:`your_domain_or_ip` with your actual domain or IP:

.. code-block:: nginx

    server {
        listen 80;
        server_name your_domain_or_ip;

        location = /favicon.ico { access_log off; log_not_found off; }

        location /static/ {
            root /opt/NCTR-Bagit-Record-Transfer;
        }

        location / {
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_pass http://unix:/opt/NCTR-Bagit-Record-Transfer/gunicorn.sock;
        }
    }


This configuration assumes you have a unix socket file set up for gunicorn at
:code:`/opt/NCTR-Bagit-Record-Transfer/gunicorn.sock`, which is not set up *yet* but we will address
this issue soon.

Enable the site by linking the configuration in the sites-enabled directory:

.. code-block:: console

    (env) $ cd /etc/nginx/
    (env) $ sudo ln -s sites-available/recordtransfer.conf sites-enabled/recordtransfer.conf


You can test if the configuration has syntax errors by using the command:

.. code-block:: console

    (env) $ sudo nginx -t


3. Gunicorn Setup
#################

.. note::

    If the application dependencies have been installed with :code:`pip` as specified above in
    section 1, gunicorn **20.0.4** will already be installed inside the application's virtual
    environment! Hooray for pure python dependencies!


`Gunicorn <https://gunicorn.org/>`_ is a WSGI server that sits between NGINX and the Django
application. NGINX forwards non-trivial requests to Gunicorn, where it interprets the HTTP requests
and forwards them to Django in a way it understands.

A systemd initialization script is not created when gunicorn is installed, so go ahead and create a
new script for gunicorn at :code:`/usr/lib/systemd/system/gunicorn.service` and add these contents:

.. code-block ::

    # file /usr/lib/systemd/system/gunicorn.service
    [Unit]
    Description=Gunicorn WSGI Daemon
    After=network.target

    [Service]
    User=nginx
    Group=nginx
    WorkingDirectory=/opt/NCTR-Bagit-Record-Transfer/bagitobjecttransfer
    ExecStart=/opt/NCTR-Bagit-Record-Transfer/env/bin/gunicorn \
        --workers 3 \
        --bind unix:/opt/NCTR-Bagit-Record-Transfer/gunicorn.sock \
        bagitobjecttransfer.wsgi

    [Install]
    WantedBy=multi-user.target


Enable the gunicorn service to start on system startup:

.. code-block:: console

    (env) $ sudo systemctl enable gunicorn


4. Redis Setup
##############

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


To set up the asynchronous RQ workers, add the following lines to the
:code:`/opt/NCTR-Bagit-Record-Transfer/.env` file:

.. code-block::

    # file /opt/NCTR-Bagit-Record-Transfer/.env
    RQ_HOST_DEFAULT=localhost
    RQ_PORT_DEFAULT=6379
    RQ_DB_DEFAULT=0
    RQ_PASSWORD_DEFAULT=
    RQ_TIMEOUT_DEFAULT=500


This is all the setup that the RQ workers need to function correctly.


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
add these lines to the environment file at :code:`/opt/NCTR-Bagit-Record-Transfer/.env`:

.. code-block::

    # file /opt/NCTR-Bagit-Record-Transfer/.env
    MYSQL_HOST=localhost
    MYSQL_DATABASE=recordtransfer
    MYSQL_USER=django
    MYSQL_PASSWORD='password'


********************************
Migrate Record Transfer Database
********************************

After MySQL is set up, you can populate the new **recordtransfer** database with the tables for the
record transfer application. This process is called *database migration*. But before migrating all
of the database tables, we need to create a *new* migration so that you can set the domain of your
website. Without doing this, many common features of the application will break.

Change to the directory that has the :code:`manage.py` script and make a new migration that you'll
edit to set the domain name of your site:

.. code-block:: console

    $ cd /opt/NCTR-Bagit-Record-Transfer/bagitobjecttransfer/
    $ python3 manage.py makemigrations --empty --name set_site_2_domain recordtransfer


A migration file is simply a Python script. Open the generated migration file to edit it. It should
be called something similar to :code:`0011_set_site_2_domain.py`. If you like vim:

.. code-block::

    $ vim recortransfer/migration/0011_set_site_2_domain.py


Make three changes to the generated Python file:

1. Add a new function that assigns your domain to ID 2 (ID 1 is set to localhost already)
2. Add a dependency to the final sites migrations
3. Add your new function from change 1 above to the :code:`operations`


.. note::

    Change YOUR_DOMAIN_HERE to the domain of your site, and YOUR_SITE_NAME_HERE to assign a name to
    the site. YOUR_DOMAIN_HERE should not include http:// or https:// and only include the domain
    name.


.. code-block:: python

    # Generated by Django 3.1.1 on 2020-11-23 16:06

    from django.db import migrations
    from django.contrib.sites.models import Site

    # Change 1: Add a new function assigning your domain to ID 2
    def update_domain(apps, schema_editor):
        Site.objects.update_or_create(
            pk=2,
            defaults={
                'domain': 'YOUR_DOMAIN_HERE',
                'name': 'YOUR_SITE_NAME_HERE'
            }
        )

    class Migration(migrations.Migration):

        dependencies = [
            ('recordtransfer', '0010_update_site_name'),
            # Change 2: Add a dependency on the final sites migration
            ('sites', '0002_alter_domain_unique'),
        ]

        operations = [
            # Change 3: Add your new function here
            migrations.RunPython(update_domain),
        ]


Save and exit that file before applying this migration and all of the other migrations:

.. code-block:: console

    $ python3 manage.py migrate


You will also want to set the domain name in the :code:`/opt/NCTR-Bagit-Record-Transfer/.env` file
while we're on the topic of the domain name:

.. code-block::

    # file /opt/NCTR-Bagit-Record-Transfer/.env
    HOST_DOMAINS=YOUR_DOMAIN_HERE


.. note::

    The domains you put in HOST_DOMAINS will be used as Django's
    `ALLOWED_HOSTS <https://docs.djangoproject.com/en/3.1/ref/settings/#allowed-hosts>`_. You can
    add more than one domain by separating domain names with spaces.


****************
Create Superuser
****************

Work in progress.


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

