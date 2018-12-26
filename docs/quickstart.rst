Quickstart
==========

If you want to have a quick look or just run the project locally, you can get started by either forking this repository
or just cloning it directly:

::

   git clone https://github.com/vitorfs/colossus.git


Ideally, create a `virtualenv <https://docs.python-guide.org/dev/virtualenvs/>`_ and install the projects dependencies:

::

   pip install -r requirements/development.txt


Create a local database:

::

   python manage.py migrate


Create a user account:

::

   python manage.py createsuperuser


Start development server:

::

   python manage.py runserver


Go to the login page on your browser:

::

   http://127.0.0.1:8000/accounts/login/


PS: Campaign scheduling will not work out-of-the-box. You need to install a message broker and
`setup Celery <https://simpleisbetterthancomplex.com/tutorial/2017/08/20/how-to-use-celery-with-django.html>`_ properly.
