===============
Django-AWS-Mail
===============

A Django email backend for Amazon's Simple Email Service (SES) v2 and utility views + signals for Amazon's Simple Notification Service (SNS).

:Author: Bas van Gaalen (http://github.com/webtweakers)
:License: MIT

.. image:: https://badge.fury.io/py/django-aws-mail.svg
    :target: https://badge.fury.io/py/django-aws-mail

Features
========

* Fully compatible with **Django 6.0+** (Modern Python Email API).
* Supports **AWS SESv2** (via boto3).
* Integrated with **AWS SNS** for bounce and complaint handling.
* Flexible configuration via Django settings or environment variables.
* Comprehensive signal support for tracking email lifecycles.

Installation
============

Install the package via pip or poetry:

.. code-block:: bash

    pip install django-aws-mail

Configuration
=============

Add the backend to your Django ``settings.py``:

.. code-block:: python

    EMAIL_BACKEND = 'django_aws_mail.backends.EmailBackend'

Usage
=====

The library provides a ``compose`` utility to easily create multipart emails (HTML and Text) using Django templates.

.. code-block:: python

    from django_aws_mail.utils import compose

    # Create the message
    message = compose(
        recipients=["customer@example.com"],
        subject="Welcome to our service!",
        template="email/welcome.html",
        context={"name": "John Doe"},
        from_email="Support <support@example.com>"
    )

    # Send it
    message.send()

Signals
=======

The library provides a rich set of signals to track the lifecycle of your emails.

Backend Signals
---------------

These fire during the ``.send()`` process within your application:

* ``mail_pre_send``: Fired before the message is sent to AWS.
* ``mail_post_send``: Fired after a successful API response from AWS.

SNS Webhook Signals
-------------------

These are triggered by AWS SNS notifications (via the provided webhook views):

* ``mail_send``: The email was successfully sent by SES.
* ``mail_delivery``: The email was successfully delivered to the recipient.
* ``mail_bounce``: The email bounced (Hard or Soft).
* ``mail_complaint``: The recipient marked the email as spam.
* ``mail_reject``: SES rejected the email (e.g., due to virus or blacklisting).
* ``mail_delivery_delay``: There is a delay in delivering the email.
* ``mail_open``: The recipient opened the email (requires SES tracking).
* ``mail_click``: The recipient clicked a link (requires SES tracking).

Example Usage:

.. code-block:: python

    from django.dispatch import receiver
    from django_aws_mail.signals import mail_bounce, mail_complaint

    @receiver(mail_bounce)
    def handle_bounce(sender, message_id, bounce_type, **kwargs):
        # Handle the bounce (e.g., deactivate the user's email)
        print(f"Email {message_id} bounced. Type: {bounce_type}")

Development
===========

To run the sandbox management command:

.. code-block:: bash

    poetry install
    poetry run manage
