Management Commands
===================

The record transfer application provides several Django management commands to help administrators perform common maintenance and configuration tasks. These commands are run from within the application container using Django's ``manage.py`` script.

Set Domain
----------

Sets the domain of the current site. If you are running the record transfer app somewhere other than your localhost, you will need to add your site's domain to the database. If you do not set the domain, your emails will not send correctly, and will have the wrong link to your site.

.. code-block:: bash

    python manage.py set_domain "my.domain.com"

**Arguments:**

* ``domain`` - The domain to set for the current site (e.g., "my.domain.com")

**Options:**

* ``--display-name`` - Optional display name to set for the current site

**Examples:**

.. code-block:: bash

    # Set domain only
    python manage.py set_domain "my.domain.com"

    # Set domain with display name
    python manage.py set_domain "my.domain.com" --display-name "My Site Name"

.. warning::
    Do not include the protocol (http:// or https://) in the domain name. Use only the domain
    itself, such as "example.com" or "subdomain.example.com".


Send Test Email
---------------

Sends test emails to verify that email functionality is working correctly. This is useful for
testing email configuration after initial setup or changes.

.. code-block:: bash

    python manage.py send_test_email <email_type> <recipient_email>

**Arguments:**

* ``email_type`` - The type of email to send (see available types below)
* ``recipient_email`` - The email address to send the test email to

**Available Email Types:**

* ``submission_creation_success`` - Email sent when a submission is successfully created
* ``submission_creation_failure`` - Email sent when submission creation fails
* ``thank_you_for_your_submission`` - Thank you email sent to submitters
* ``your_submission_did_not_go_through`` - Email sent when submission processing fails
* ``user_activation_email`` - Email sent to activate new user accounts
* ``user_account_updated`` - Email sent when user account information is updated
* ``user_in_progress_submission_expiring`` - Email sent when in-progress submissions are expiring

**Examples:**

.. code-block:: bash

    # Test user activation email
    python manage.py send_test_email user_activation_email admin@example.com

    # Test submission success email
    python manage.py send_test_email submission_creation_success user@example.com


Reset App
---------

Resets application data to a clean state. This command is designed for development and
testing purposes to restore the application to its initial state. This command is
disabled in production environments for safety and only works with SQLite3 databases.

.. code-block:: bash

    python manage.py reset

**Options:**

* ``--seed`` - Populate the database with seed data and required uploaded files after resetting it
* ``--no-confirm`` - Skip confirmation prompt before resetting the database

**Examples:**

.. code-block:: bash

    # Basic reset with confirmation prompt
    python manage.py reset

    # Reset and populate with seed data
    python manage.py reset --seed

    # Reset without confirmation prompt (useful for scripts)
    python manage.py reset --no-confirm

    # Reset with seed data and no confirmation
    python manage.py reset --seed --no-confirm

**What this command does:**

* Completely removes the development database file (SQLite3 only)
* Recreates the database schema by running all migrations
* Optionally loads seed data and sets up uploaded files (with ``--seed`` flag)
* Restores the application to a clean starting point


Getting Help
############

You can get help for any management command by using the ``--help`` flag:

.. code-block:: bash

    python manage.py <command> --help

This will display detailed information about the command's arguments, and options.

You can also list all available management commands:

.. code-block:: bash

    python manage.py help
