# Colossus

[![Build Status](https://travis-ci.com/vitorfs/colossus.svg?branch=master)](https://travis-ci.com/vitorfs/colossus)
[![codecov](https://codecov.io/gh/vitorfs/colossus/branch/master/graph/badge.svg)](https://codecov.io/gh/vitorfs/colossus)
[![Documentation Status](https://readthedocs.org/projects/colossus/badge/?version=latest)](https://colossus.readthedocs.io/en/latest/?badge=latest)

Self-hosted email marketing solution. Compatible with any SMTP email service.

## Screenshots

![Colossus new campaign](https://colossus.readthedocs.io/en/latest/_images/colossus-new-campaign.png)

![Colossus campaigns](https://colossus.readthedocs.io/en/latest/_images/colossus-campaigns.png)

[More Colossus screenshots.](https://colossus.readthedocs.io/en/latest/features.html#screenshots)

## Features

* Create and manage multiple mailing lists;
* Import lists from other providers (csv files or paste email addresses);
* Create reusable email templates;
* Customize sign up pages (subscribe, unsubscribe, thank you page, etc.);
* Default double opt-in for sign ups;
* Schedule email campaign to send on a specific date and time;
* Track email opens and clicks;
* Change link URL after email is sent;
* Reports with geolocation;
* Compatible with Mailgun, SendGrid, Mandrill, or any other SMTP email service.

## Requirements

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/)
- [uv](https://github.com/astral-sh/uv) (required only for image build, installed inside the container)
- [Make](https://www.gnu.org/software/make/) (optional, for convenient command execution)

## Versions

- **Python:** >=3.9
- **Django:** 2.1.5
- **Celery:** 4.2.1
- **beautifulsoup4:** 4.7.1
- **dj-database-url:** 0.5.0
- **django-crispy-forms:** 1.7.2
- **django-debug-toolbar:** 1.11
- **django-ratelimit:** 2.0.0
- **geoip2:** 2.9.0
- **gunicorn:** 19.9.0
- **html2text:** 2018.1.9
- **psycopg2-binary:** 2.8.6
- **python-decouple:** 3.1
- **pytz:** 2018.9
- **raven:** 6.10.0
- **requests:** 2.21.0
- **setuptools:** >=80.9.0
- **whitenoise:** 4.1.2

PostgreSQL and RabbitMQ are optional dependencies. You can use other databases supported by Django and other message brokers compatible with Celery.

jQuery is mainly a Bootstrap dependency. There is very little JavaScript code in the project—mostly plain Django and HTML templates.

All package versions are specified in [pyproject.toml](./pyproject.toml) and [uv.lock](./uv.lock).

## Quickstart (Docker)

1. Clone the repository:

```sh
git clone git@github.com:vitorfs/colossus.git
cd colossus
```

2. Create a `.env` file in the project root and specify the required environment variables. You can use [.env.example](./.env.example) as a template for all required and optional variables.

3. Start the project using Docker Compose:

- To run with SQLite (default):

```sh
make debug
```
or directly:
```sh
mkdir -p ./data
docker compose up --build --detach
```

- To run with PostgreSQL:

```sh
make release
```
or directly:
```sh
mkdir -p ./data
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up --build -d
```

4. Stop the services:

```sh
make stop
```
or
```sh
docker compose down
```

5. Full cleanup (containers, images, volumes):

```sh
make clean
```
or
```sh
rm -rf ./data
docker compose -f docker-compose.yml -f docker-compose.postgres.yml down --volumes --rmi all --remove-orphans
```

6. Open your browser and go to the admin setup page:

```
http://127.0.0.1:8000/setup/
```
You can automate admin creation by defining the following variables in your .env file: ADMIN_LOGIN, ADMIN_PASS, and ADMIN_EMAIL.

> **Note:** For campaign scheduling to work, Celery and a message broker (RabbitMQ) are required. They are already configured in docker-compose.

## Documentation

This is a pre-release of the project; full documentation and user guides are in development.

For now, you will only find documentation of the internal APIs in the source code.

[colossus.readthedocs.io](https://colossus.readthedocs.io)

## Who's using Colossus?

Currently, just the author. It is used for the [simpleisbetterthancomplex.com](https://simpleisbetterthancomplex.com/) blog newsletter.

Example signup page: [sibt.co/newsletter](https://sibt.co/newsletter)

## License

The source code is released under the [MIT License](https://github.com/vitorfs/colossus/blob/master/LICENSE).
