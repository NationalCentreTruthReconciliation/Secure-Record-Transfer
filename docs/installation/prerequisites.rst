Pre-Requisites to Running
=========================

This page contains installation info on all of the software required to get the app up and running.
Ideally, you will be running the application on Linux, since you will have a lot of difficulty
getting Redis and Django-RQ to work on Windows.


***
Git
***

If you are planning on doing any sort of development on this application, it is highly recommended
to install the git command line tool. To install Git, follow `these instructions
<https://git-scm.com/download/linux>`_. If you do not want to install git, you may download the
source code rather than cloning the repository. The instructions for that are in the
:ref:`Without git clone` section below.

***********
Source Code
***********

You may get the source code for this app using the git command line tool or without it.

Using git clone
###############

Using your favourite command shell, :code:`cd` to the directory you want the source code repository
to download to. Run the following command to clone the code into your current directory:

.. code-block:: console

    $ git clone https://github.com/danloveg/NCTR-Bagit-Record-Transfer.git

Without git clone
#################

In your favourite browser, go to https://github.com/danloveg/NCTR-Bagit-Record-Transfer. Click the
**Code** button and select **Download ZIP**. Choose whichever folder you want the code to go into.
Extract the ZIP once it has downloaded.

******
Python
******

Since the app is built using Django, a Python-based web framework, you will need to install Python
to run the app. Install Python 3.6.x using `this guide
<https://docs.python-guide.org/starting/install3/linux/>`_.

Once you are sure Python 3.6 is installed, navigate to the top level of the cloned or downloaded
repository using your favourite command shell. You will need to create a virtual environment to run
the app out of. Using a virtual environment ensures that all of your python packages are the correct
version. To create a new environment, use:

.. code-block:: console

    $ python3 -m venv env/

Once your environment is created, make sure it is active. You can tell if the environment is active
if your command prompt now starts with **(env)**. The following activates the environment if it is
not already:

.. code-block:: console

    $ source env/bin/activate

Once your virtual environment is active, you can install the required packages from the
requirements.txt file at the top level of the repository. To do so:

.. code-block:: console

    $ python3 -m pip install -r requirements.txt

This will install every Python package you could need, including Django.

*****
Redis
*****

This app uses a Redis server for logging background task information, along with Django-RQ as a
broker to the Redis server. Provided you installed all of the required packages in the
requirements.txt file, you will already have Django-RQ installed in your virtual environment. All
that's left to do is install Redis itself. You can download redis from the download page on the
`Redis website <https://redis.io/download>`_. Note that Django-RQ only supports Redis version
3.0 and up, so make sure you install at least version 3.0.

*****
Nginx
*****

If you want to deploy your application in a production environment, we recommend using Nginx. If you
only want to run the application locally, the server bundled with Django is an excellent option, and
if you installed all of the required packages using the instructions above, you already have the
Django dev server.

***********
SMTP Server
***********

TBD

********
Database
********

We recommend using MySQL as a database for production, but for development, SQLite works fine. You
can find installation info for MySQL on the `MySQL website
<https://dev.mysql.com/doc/refman/8.0/en/installing.html>`_.
Note that Django only supports MySQL 5.6 and up, so make sure you install at least version 5.6.
