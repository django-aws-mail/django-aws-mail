import logging

from django.dispatch import receiver
from django.contrib.auth import get_user_model

from django_aws_mail.signals import mail_delivery, mail_delivery_delay, mail_bounce, mail_complaint
from django_aws_mail.models import Delay, Bounce, Complaint

User = get_user_model()

logger = logging.getLogger(__name__)


@receiver(mail_delivery)
def handle_delivery(sender, mail, event, message, **kwargs):
    logger.debug(f'Message delivered:\n{message}\n')


@receiver(mail_delivery_delay)
def handle_delay(sender, mail, event, message, **kwargs):
    logger.debug(f'Message delayed:\n{message}\n')

    email = mail['destination'][0]
    try:
        user = User.objects.get(email=email.lower())
    except User.DoesNotExist:
        user = None

    # log delay
    obj, created = Delay.objects.get_or_create(
        destination=email,
        delay_type=event.get('delayType'),
        defaults={'user': user, 'delay': event, 'mail': mail})

    if not created:
        obj.user = user
        obj.delay = event
        obj.mail = mail
        obj.count += 1
        obj.save()


@receiver(mail_bounce)
def handle_bounce(sender, mail, event, message, **kwargs):
    logger.debug(f'Message bounced:\n{message}\n')

    email = mail['destination'][0]
    try:
        user = User.objects.get(email=email.lower())
    except User.DoesNotExist:
        user = None

    # log bounce
    obj, created = Bounce.objects.get_or_create(
        destination=email,
        bounce_type=event.get('bounceType'),
        bounce_sub_type=event.get('bounceSubType'),
        defaults={'user': user, 'bounce': event, 'mail': mail})

    if not created:
        obj.user = user
        obj.bounce = event
        obj.mail = mail
        obj.count += 1
        obj.save()


@receiver(mail_complaint)
def handle_complaint(sender, mail, event, message, **kwargs):
    logger.debug(f'Message complaint:\n{message}\n')

    email = mail['destination'][0]
    try:
        user = User.objects.get(email=email.lower())
    except User.DoesNotExist:
        user = None

    # log complaint
    obj, created = Complaint.objects.get_or_create(
        destination=email,
        complaint_type=event.get('complaintSubType'),
        defaults={'user': user, 'complaint': event, 'mail': mail})

    if not created:
        obj.user = user
        obj.complaint = event
        obj.mail = mail
        obj.count += 1
        obj.save()
