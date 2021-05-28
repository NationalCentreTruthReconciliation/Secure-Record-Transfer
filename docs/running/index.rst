Running the App
===============

There are two documented ways to start up the application mentioned here.

The simplest method is to run the application using :code:`docker-compose`. This starts up all of
the required services for you, and there is minimal manual work involved.

The other method outlines how we configured the application to run in a production environment.

The Docker and running configurations uses a simple `MailHog <https://github.com/mailhog/MailHog>`_
server to intercept messages coming from the application. Visiting http://localhost:8025 when the
app is running allows you to visit the MailHog dashboard, which lets you view all of the emails sent
by the app. This is miles better than sending emails to the console!

.. toctree ::
    :maxdepth: 1

    docker
    production
