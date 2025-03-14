Running the App
===============

It is recommended to run this application with  `Podman <https://podman.io/>`_ (or alternately
`Docker <https://www.docker.com/>`_). The following documentation assumes you are using Podman, but
if you are using Docker, substitute the relevant Docker commands.

Before running the application, make sure you have these tools installed:

- `Podman <https://podman.io/>`_
- `Podman Desktop <https://podman-desktop.io/>`_ (Optional, but recommended)
- `Python 3 <https://python.org>`_
- `Podman Compose <https://github.com/containers/podman-compose>`_


Development Application
-----------------------

The simplest way to run the application is in "development" mode. **If you just want to try the
application out, follow these steps**.

To start the application, run this command:

.. code-block:: bash

    podman-compose -f compose.dev.yml up -d


Visit http://localhost:8000 to see the application running.

To stop the application, run the :code:`down` command:

.. code-block:: bash

    podman-compose -f compose.dev.yml down


If you are using `Podman Desktop <https://podman-desktop.io/>`_, you should now see the application
and all of its services running there, too.

You will find that you cannot log in to the application. You can create a new administrator
user by running the following command.

.. code-block:: bash

    podman-compose -f compose.dev.yml exec app python manage.py createsuperuser


The development application uses a simple `Mailpit <https://github.com/axllent/mailpit>`_ server to
intercept messages coming from the application. Visiting http://localhost:8025 when the app is
running allows you to visit the Mailpit dashboard, which lets you view all of the emails sent by
the app.

If you would like to create new users via the sign-up page, you can find the account activation
emails in Mailpit.

The logging configuration for the application can be found in the file :code:`app/settings/docker_dev.py`.
The logs are all written to stdout, which is captured by Podman (or Docker).

To view logs for a given container (the *app* container, in this case), you may run a command like
this:

.. code-block:: bash

    podman-compose -f compose.dev.yml logs -f app


The logs can also be found easily in Podman Desktop by clicking on a specific container.


Debugging the Development Application
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To debug the application, `view the setup in the DEVELOPERS.md file <https://github.com/NationalCentreTruthReconciliation/Secure-Record-Transfer/blob/master/DEVELOPERS.md>`_.


Production Application
----------------------

The production Docker environment uses Nginx + Gunicorn instead of the Django development server,
and opts to use MySQL instead of SQLite.

From the root of the repository, run the following commands before running the application in
"production mode" for the first time.

.. code-block:: bash

    cp example.prod.env .prod.env


The settings in the :code:`.prod.env` file control the application, as well as some other settings
Django loads. Refer to :ref:`Application Settings` for application
settings, and refer to the file :code:`app/settings/docker_prod.py` for more
settings that can be controlled by the :code:`.prod.env` file. The :code:`example.prod.env` file
contains most of the settings you are likely to be interested in changing.

Similar to the development application, you run the production application using Docker or Podman,
but pass it the production compose file instead.

.. code-block:: bash

    podman-compose -f compose.prod.yml up -d


After the app starts up, you can create an admin superuser with the following command:

.. code-block:: bash

    podman-compose -f compose.prod.yml exec app python manage.py createsuperuser


Logs for each container can be accessed with the :code:`logs` command:

.. code-block:: bash

    podman-compose -f compose.prod.yml logs -f app


Domain Setup
^^^^^^^^^^^^

After starting the app up, you will need to set the domain so that emails send correctly. To do
that, refer to the section of the docs on :ref:`Updating the Domain of Your Site`.

Nginx Configuration
^^^^^^^^^^^^^^^^^^^

The Nginx configuration file can be found in :code:`docker/nginx/templates/nginx.conf.template`.
This is a configuration *template* that syncs the NGINX configuration with the :ref:`File Upload Controls`
settings and both the `STATIC_ROOT <https://docs.djangoproject.com/en/4.2/ref/settings/#static-root>`_
and `MEDIA_ROOT <https://docs.djangoproject.com/en/4.2/ref/settings/#media-root>`_. The values for
these environment variables are set in the compose file and the :code:`.prod.env` file.


MySQL Configuration
^^^^^^^^^^^^^^^^^^^

The MySQL configuration file can be found in :code:`docker/mysql/mysqld.cnf`.


Redis Configuration
^^^^^^^^^^^^^^^^^^^

The Redis configuration file can be found in :code:`docker/redis/redis.conf`.


ClamAV Configuration
^^^^^^^^^^^^^^^^^^^^

The ClamAV configuration files can be found in the folder :code:`docker/clamav`.
