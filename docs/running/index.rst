Running the App
===============

There are three documented ways to start up the application mentioned here.

The simplest method is to run the application using :code:`docker-compose`. This starts up all of
the required services for you, and there is minimal manual work involved.

The next method is running the application with a mixture of running services in Docker containers
and your local machine. This method is preferred if you are intending to debug the application or
you want to do any sort of development on it.

The final method outlines how we configured the application to run in a production environment.

Both the Docker and local running configurations use a simple
`MailHog <https://github.com/mailhog/MailHog>`_ server to intercept messages coming from the
application. Visiting http://localhost:8025 when the app is running allows you to visit the
MailHog dashboard, which lets you view all of the emails sent by the app. This is miles better than
sending emails to the console!

.. toctree ::
    :maxdepth: 1

    docker
    local
    production
