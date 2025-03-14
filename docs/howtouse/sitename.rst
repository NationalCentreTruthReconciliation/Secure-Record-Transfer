Updating the Domain of Your Site
================================

If you are running the record transfer app somewhere other than your localhost, you will need to add
your site's domain to the database. If you do not set the domain, your emails will not send
correctly, and will have the wrong link to your site.

To set the domain of your site, run the following command from the :code:`app` directory **within
the container**:

.. code-block:: shell

    python manage.py set_domain "my.domain.com"

replacing :code:`my.domain.com` with your site's fully qualified domain name.

If you also want to set an optional display name for your site, you can use the
:code:`--display-name` flag:

.. code-block:: shell

    python manage.py set_domain "my.domain.com" --display-name "My Site Name"

replacing "My Site Name" with your desired display name.