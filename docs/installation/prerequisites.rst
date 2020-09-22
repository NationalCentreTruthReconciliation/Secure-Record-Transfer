Pre-Requisites to Running
=========================

This page contains installation info on all of the software required to get the app up and running.
Ideally, you will be running the application on Linux, since you will have a lot of difficulty
getting Redis and Django-RQ to work on Windows.


***
Git
***

If you are planning on doing any sort of development on this application, it is highly recommended
to install the git command line tool. If you do not want to install git, you may download the source
code rather than cloning to repository. The instruction for that are in the :ref:`Without git clone`
section.

***********
Source Code
***********

You may get the source code for this app using the git command line tool or without it.

Using git clone
###############

Using the git command line, cd to the directory you want the repo in, and

Without git clone
#################

Without git clone!

******
Python
******

First and foremost, you will need Python. Install Python 3.6.x using this guide:
https://docs.python-guide.org/starting/install3/linux/.

Once you are sure Python 3.6 is installed, navigate to the top level of the cloned repository using
your favourite command shell.

First, create a virtual environment to run the app out of. Using a virtual environment ensures that
all of your python packages are the correct version. To create the environment, use:

.. code-block:: console

    $ python -m venv env/

Once your environment is created, make sure it is active. You will know if its active if your
command prompt now starts with **(env)**. The following activates the environment if it not already:

.. code-block:: console

    $ source env/bin/activate

Once your virtual environment is active, you can install the required packages from the
requirements.txt file at the top level of the repository. To do so:

.. code-block:: console

    $ python -m pip install -r requirements.txt

This will install every Python package you could need, including Django.

*****
Redis
*****

This app uses a Redis server for logging background task information, along with Django-RQ as a
broker to the Redis server. Provided you installed all of the required packages in the
requirements.txt file, you will already have Django-RQ installed in your virtual environment. All
that's left to do is install Redis itself. You can download redis from the download page on the
Redis website here https://redis.io/download. Note that Django-RQ only supports Redis version 3.0
and up, so make sure you install at least version 3.0.

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
can find installation info for MySQL here https://dev.mysql.com/doc/refman/8.0/en/installing.html.
Note that Django only supports MySQL 5.6 and up, so make sure you install at least version 5.6.
