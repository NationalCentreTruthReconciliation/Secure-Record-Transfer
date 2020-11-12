Running with Docker Compose
===========================

The easiest way to run the application is to run the entire thing with Docker. This is the preferred
method to run the app if you aren't doing any sort of development on the app. If you do want to work
on the Django app's backend, refer to the section on :ref:`Running Locally for Development`.

First, make sure you've installed Docker. Create an environment file called :code:`.dockerenv` in
the :code:`bagitobjecttransfer` folder. Put these contents in it if it's not already created:

.. code-block::

    BAG_FOLDER_LINUX = /app/media/bags


After ensuring you have a minimal environment file set up, make sure you are in the
:code:`bagitobjecttransfer` folder, and run all of the services with Docker:

.. code-block:: console

    $ docker-compose up -d


If this is your first time running the app in this configuration, you will first want to populate
the database tables and create a super user before visiting the app in your browser. To do so,
execute the following commands to run a shell in the Django app container, migrate the database,
and create a super user (before exiting):

.. code-block:: console

    $ docker-compose exec app sh
    $ python3 manage.py migrate
    $ python3 manage.py createsuperuser
    $ exit


You should now be able to access the app at http://127.0.0.1:8000 or http://localhost:8000 in your
favourite browser.

Any emails that the app sends are intercepted by the MailHog server. You can see the emails by
visiting http://localhost:8025 in your favourite browser.

.. note::

    The logs are disabled for the mail server since they are too verbose. To re-enable them, remove
    the :code:`logging` section for the email service in the :code:`docker-compose.yml` file.
