from email.utils import formataddr

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_spaces_between_tags

from django_aws_mail import settings
from django_aws_mail.html import HTMLParser


def compose(recipients, subject, template, context=None, from_email=None, **kwargs):
    """
    Create a multipart MIME email message, by rendering html and text body.
    Optionally add SES headers config_set and mail_type to the kwargs.
    """
    # sanitize input: subject, recipients, from email
    subject = ''.join(subject.splitlines())
    if not isinstance(recipients, list):
        recipients = [recipients]
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL
    if not isinstance(from_email, str):
        from_email = formataddr(from_email)

    # render html content
    context = context or {}
    html = render_to_string(template, context).strip()
    html = strip_spaces_between_tags(html)

    # convert html to text
    parser = HTMLParser()
    parser.feed(html)
    parser.close()
    text = parser.text()

    # get optional headers
    headers = {}
    if 'headers' in kwargs:
        headers = kwargs.pop('headers')
    if 'config_set' in kwargs:
        headers['X-Ses-Configuration-Set'] = kwargs.pop('config_set')
    if 'mail_type' in kwargs:
        headers['X-Ses-Message-Tags'] = f"mail-type={kwargs.pop('mail_type')}"

    # create email message
    message = EmailMultiAlternatives(subject, text, from_email, recipients, headers=headers, **kwargs)
    message.attach_alternative(html, 'text/html')
    return message
