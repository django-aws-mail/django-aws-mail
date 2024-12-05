import re
from email.utils import formataddr

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_spaces_between_tags

from django_aws_mail import settings
from django_aws_mail.html import HTMLParser


def compose(
        recipients,
        subject,
        html_template,
        text_template=None,
        context=None,
        from_email=None,
        ses_configuration_set=None,
        ses_mail_type_tag=None):

    """
    Create a multipart MIME email message, by rendering html and text body.
    """
    # sanitize input: subject, recipients, from
    subject = ''.join(subject.splitlines())

    if not isinstance(recipients, list):
        recipients = [recipients]

    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL
    if not isinstance(from_email, str):
        from_email = formataddr(from_email)

    context = context or {}

    # render content
    html = render_to_string(html_template, context).strip()
    html = strip_spaces_between_tags(html)
    if text_template:
        text = render_to_string(text_template, context).strip()
    else:
        # convert html to text and cleanup
        parser = HTMLParser()
        parser.feed(html)
        parser.close()
        text = parser.text()

    # remove excessive white-space
    text = re.sub(r'( {2,})', '', text)
    text = re.sub(r'(\s{3,})', '\n\n', text)

    # create message
    message = EmailMultiAlternatives(subject, text, from_email, to=recipients)
    message.attach_alternative(html, 'text/html')

    # attach SES specific headers
    if ses_configuration_set:
        message.extra_headers['X-Ses-Configuration-Set'] = ses_configuration_set
    if ses_mail_type_tag:
        message.extra_headers['X-Ses-Message-Tags'] = f'mail-type={ses_mail_type_tag}'

    return message
