# Colossus

[![Build Status](https://travis-ci.org/vitorfs/colossus.svg?branch=master)](https://travis-ci.org/vitorfs/colossus)
[![codecov](https://codecov.io/gh/vitorfs/colossus/branch/master/graph/badge.svg)](https://codecov.io/gh/vitorfs/colossus)

Self-hosted email marketing solution

![Colossus new campaign](https://colossus.readthedocs.io/en/latest/_images/colossus-new-campaign.png)

![Colossus campaigns](https://colossus.readthedocs.io/en/latest/_images/colossus-campaigns.png)

[More Colossus screenshots.](https://colossus.readthedocs.io/en/latest/features.html#screenshots)

## Features

* Create and manage multiple mailing lists
* Import lists from other providers (csv files or paste email addresses)
* Create reusable email templates
* Customize sign up pages (subscribe, unsubscribe, thank you page, etc.)
* Default double opt-in for sign ups
* Schedule email campaign to send on a specific date and time
* Track email opens and clicks
* Reports with geolocation

## Tech Specs

* Python 3.6
* Django 2.1
* PostgreSQL 10
* Celery 4.2
* RabbitMQ 3.7
* Bootstrap 4 
* jQuery 3.3

PostgreSQL and RabbitMQ are soft dependencies. Other databases (supported by Django) can easily be used as well as other message broker compatible with Celery.

Complete list of Python dependencies can be found in the requirements files.

## Documentation

This is just a pre-release of the project and I still have to work on a proper documentation and user guides.

For now you will only find documentation of the internal APIs in the source code.

[colossus.readthedocs.io](https://colossus.readthedocs.io)

## Who's using Colossus?

Right now just myself. I'm currently using it for my blog newsletter at [simpleisbetterthancomplex.com](https://simpleisbetterthancomplex.com/).

Here is how my sign up page looks like: [sibt.co/newsletter](https://sibt.co/newsletter)

## License

The source code is released under the [MIT License](https://github.com/vitorfs/colossus/blob/master/LICENSE).
