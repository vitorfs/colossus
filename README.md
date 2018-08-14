# Colossus

[![Build Status](https://travis-ci.org/vitorfs/colossus.svg?branch=master)](https://travis-ci.org/vitorfs/colossus)
[![codecov](https://codecov.io/gh/vitorfs/colossus/branch/master/graph/badge.svg)](https://codecov.io/gh/vitorfs/colossus)

Self-hosted email marketing solution

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
