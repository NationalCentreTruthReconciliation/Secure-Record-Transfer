Deploying in Production
=======================

The setup for a production build is much more involved than the development and Docker methods.

To manage services, systemd is used. The OS used for this guide is Red Hat Enterprise Linux 7. There
may be some differences if you intend to deploy the app on a different Linux distribution, but the
basics should be the same.

Redis Setup
###########

.. note::

    We are using Redis version **3.2.12**. You can
    `download version 3.2.12 here <http://download.redis.io/releases/redis-3.2.12.tar.gz>`_.


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


You should now be able to start the redis service with the following command:

.. code-block:: console

    $ sudo service redis start


Environment Setup
#################

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

