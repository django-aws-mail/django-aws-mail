===============
Django-AWS-Mail
===============

A Django email backend for Amazon's Simple Email Service (SES) v2 and utility views + signals for Amazon's Simple Notification Service (SNS).

:Author: Bas van Gaalen (http://github.com/webtweakers)
:License: MIT

.. image:: https://img.shields.io/pypi/v/django-aws-mail.svg
    :target: https://pypi.org/project/django-aws-mail/

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

Environment Variables
---------------------

The library automatically detects the following environment variables (or Django settings). Copy ``example.env`` to ``.env`` to get started:

.. code-block:: text

    MAIL_AWS_REGION_NAME=eu-west-1
    MAIL_AWS_ACCESS_KEY_ID=ABC123
    MAIL_AWS_SECRET_ACCESS_KEY=S3cr3t

    MAIL_AWS_SNS_TOPIC_ARN=arn:aws:sns:eu-west-1:123:abc
    MAIL_AWS_SNS_VERIFY_NOTIFICATION=true
    MAIL_AWS_SNS_VERIFY_CERTIFICATE=true

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

These are triggered by AWS SNS notifications via the provided webhook views.
For more information on the contents of these notifications, see the `AWS SES documentation <https://docs.aws.amazon.com/ses/latest/dg/notification-contents.html>`_.

* ``mail_send``: The email was successfully sent by SES.
* ``mail_delivery``: The email was successfully delivered to the recipient.
* ``mail_bounce``: The email bounced (Hard or Soft).
* ``mail_complaint``: The recipient marked the email as spam.
* ``mail_reject``: SES rejected the email (e.g., due to virus or blacklisting).
* ``mail_delivery_delay``: There is a delay in delivering the email.
* ``mail_open``: The recipient opened the email (requires SES tracking).
* ``mail_click``: The recipient clicked a link (requires SES tracking).

Signal Example:

.. code-block:: python

    from django.dispatch import receiver
    from django_aws_mail.signals import mail_bounce

    @receiver(mail_bounce)
    def handle_bounce(sender, mail, event, message, **kwargs):
        # Retrieve info from the event dictionary
        bounce_type = event.get('bounceType')
        message_id = mail.get('messageId')

        print(f"Email {message_id} bounced. Type: {bounce_type}")

Development
===========

To run the sandbox management command:

.. code-block:: bash

    poetry install
    poetry run manage

To run tests and get the coverage:

.. code-block:: bash

    poetry run manage test django_aws_mail

    poetry run coverage run sandbox/manage.py test django_aws_mail

    poetry run coverage report

    poetry run coverage html
