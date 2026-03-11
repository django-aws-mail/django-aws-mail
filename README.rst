Django-AWS-Mail
===============

:Info: A Django email backend for Amazon's Simple Email Service (SES) and views + signals for Amazon's Simple Notification Service (SNS).

:Author: Bas van Gaalen (http://github.com/webtweakers)

.. image:: https://badge.fury.io/py/django-aws-mail.svg
    :target: https://badge.fury.io/py/django-aws-mail


Usage
=====
To install the requirements you'll first have to run this command:

`poetry install`

You may need to run the following command in order for .env files to be read:

`poetry self add poetry-plugin-dotenv`

Just type this on the command line from the root directory:

`poetry run manage`


Configuration
=============
Make sure to have `AUTH_USER_MODEL` and `DEFAULT_FROM_EMAIL` defined in your Django settings.

Have a look at the `example.env` file and copy it to `.env` with your AWS configuration.
You can also configure those values directly in your Django settings, if you prefer.

These values should be defined:

```
MAIL_AWS_REGION_NAME=eu-west-1
MAIL_AWS_ACCESS_KEY_ID=ABC123
MAIL_AWS_SECRET_ACCESS_KEY=S3cr3t

MAIL_AWS_SNS_TOPIC_ARN=arn:aws:sns:eu-west-1:123:abc
MAIL_AWS_SNS_VERIFY_NOTIFICATION=true
MAIL_AWS_SNS_VERIFY_CERTIFICATE=true
```
