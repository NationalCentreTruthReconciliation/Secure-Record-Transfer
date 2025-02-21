Updating the Domain of Your Site
================================

If you are running the record transfer app somewhere other than your localhost, you will need to add
your site's domain to the database. If you do not set the domain, your emails will not send
correctly, and will have the wrong link to your site.

To set the domain of your site, run the following command from the `app` directory:

.. code-block:: shell

    python manage.py set_domain "https://my.domain.com"

replacing `https://my.domain.com` with your site's domain.