from email.utils import formataddr

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_spaces_between_tags

from django_aws_mail import settings
from django_aws_mail.html import HTMLParser


def compose(recipients, subject, template, context=None, from_email=None, **kwargs):
    """
    Create a multipart MIME email message, by rendering html and text body.
    Optionally add ses_configuration_set and ses_mail_type_tag to the kwargs.
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

    # create email message
    message = EmailMultiAlternatives(subject, text, from_email, recipients)
    message.attach_alternative(html, 'text/html')

    # attach optional SES specific headers
    if 'ses_configuration_set' in kwargs:
        message.extra_headers['X-Ses-Configuration-Set'] = kwargs['ses_configuration_set']
    if 'ses_mail_type_tag' in kwargs:
        message.extra_headers['X-Ses-Message-Tags'] = f"mail-type={kwargs['ses_mail_type_tag']}"

    return message
