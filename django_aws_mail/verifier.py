import re
import json
import base64
import logging
import requests

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography import x509

from django.core.cache import cache

from django_aws_mail import settings

logger = logging.getLogger(__name__)


class NotificationVerifier(object):
    """
    Class for validating Amazon SNS event notification messages as described here:
    https://docs.aws.amazon.com/sns/latest/dg/sns-verify-signature-of-message.html
    """
    required_notification_fields = {
        'Type', 'Message', 'Timestamp', 'Signature',
        'SignatureVersion', 'TopicArn', 'MessageId',
        'SigningCertURL'
    }

    allowed_notification_types = [
        'Notification', 'SubscriptionConfirmation', 'UnsubscribeConfirmation'
    ]

    def __init__(self, request):
        self._request = request
        self._verified = None
        self._notification = None
        self._message = None

    @property
    def is_verified(self):
        if self._verified is None:
            # checks must be run in this order
            self._verified = all([
                self.check_topic_header(),
                self.check_message_type_header(),
                self.check_notification(),
                self.check_keys(),
                self.check_type(),
                self.check_signature(),
                self.check_cert(),
            ])
        return self._verified

    def check_topic_header(self):
        # if necessary, check that the topic is correct
        if hasattr(settings, 'AMAZON_SNS_TOPIC_ARN'):

            # confirm that the proper topic header was sent
            if 'HTTP_X_AMZ_SNS_TOPIC_ARN' not in self._request.META:
                logger.warning(f'Notification has no TopicArn header')
                return False

            # check to see if the topic is in the settings
            # bounces and complaints can come from multiple topics
            # AMAZON_SNS_TOPIC_ARN is a list
            topic_hdr = self._request.META['HTTP_X_AMZ_SNS_TOPIC_ARN']
            if topic_hdr not in settings.AMAZON_SNS_TOPIC_ARN:
                logger.warning(f"Notification contains bad topic: {topic_hdr}")
                return False

        return True

    def check_message_type_header(self):
        message_type_hdr = self._request.META['HTTP_X_AMZ_SNS_MESSAGE_TYPE']
        if message_type_hdr not in self.allowed_notification_types:
            logger.info(f"Unknown message type header {message_type_hdr}")
            return False
        return True

    def check_notification(self):
        """
        This check unpacks the notification from the request body and stores it locally!
        """
        request_body = self._request.body.decode('utf-8')
        try:
            self._notification = json.loads(request_body)
        except ValueError as e:
            logger.warning(f'Notification contains invalid JSON: {e}',
                           extra={'request': request_body})
            return False
        return True

    def check_keys(self):
        # ensure that the notification contains all the expected keys
        if not self.required_notification_fields <= self._notification.keys():
            logger.warning('Notification is missing required keys')
            return False
        return True

    def check_type(self):
        # ensure that the type of notification is one we'll accept
        if self._notification.get('Type') not in self.allowed_notification_types:
            logger.info(f"Unknown notification type {self._notification.get('Type')}")
            return False
        return True

    def check_signature(self):
        if self._notification.get('SignatureVersion') != '1':
            logger.warning('Invalid signature version. Unable to verify signature.')
            return False
        return True

    def check_cert(self):
        cert_url = self._notification.get('SigningCertURL')

        # confirm that the signing certificate is hosted on a correct domain
        # AWS by default uses sns.{region}.amazonaws.com
        pattern = r'^https://sns\.[-a-z0-9]+\.amazonaws\.com/'
        if not re.search(pattern, cert_url):
            logger.warning(f'Invalid certificate URL: {cert_url}')
            return False

        # verify that the notification is signed by Amazon
        if getattr(settings, 'AWS_SNS_VERIFY_CERTIFICATE', True):
            # get certificate
            pem_data = self.get_keyfile(cert_url)
            if not pem_data:
                return False
            cert = x509.load_pem_x509_certificate(pem_data)

            # get decoded signature
            signature = self._notification.get('Signature')
            if not signature:
                return False
            signature = bytes(base64.b64decode(signature))

            # retrieve canonical message data
            message = self.get_canonical_message()
            if not message:
                return False

            # figure out hash algorythm based on signature version
            signature_version = self._notification['SignatureVersion']
            if signature_version == '1':
                hash_algo = hashes.SHA1()
            elif signature_version == '2':
                hash_algo = hashes.SHA256()
            else:
                return False

            # verify message using cert public key and signature
            public_key = cert.public_key()
            try:
                public_key.verify(signature, message, padding.PKCS1v15(), hash_algo)
            except InvalidSignature:
                logger.error('Notification certificate verification failure')
                return False

        return True

    def check_message(self):
        """
        This check unpacks the message from the notification and stores it locally!
        This check is _not_ run with the other checks, so a http 200 can be returned.
        """
        try:
            self._message = json.loads(self._notification.get('Message'))
        except ValueError as e:
            # This message is not JSON. But we need to return a 200 status code
            # so that Amazon doesn't attempt to deliver the message again
            logger.warning(f'Invalid JSON Message Received: {e}',
                           extra={'notification': self._notification})
            return False
        return True

    def get_canonical_message(self):
        """
        Retrieve canonical message from Amazon SNS message, based on the notification type.
        :return: message as bytes
        """
        notification_type = self._notification.get('Type')
        if notification_type == 'Notification':
            if "Subject" in self._notification:
                fields = ['Message', 'MessageId', 'Subject', 'Timestamp', 'TopicArn', 'Type']
            else:
                fields = ['Message', 'MessageId', 'Timestamp', 'TopicArn', 'Type']
        elif notification_type in ['SubscriptionConfirmation', 'UnsubscribeConfirmation']:
            fields = ['Message', 'MessageId', 'SubscribeURL', 'Timestamp', 'Token', 'TopicArn', 'Type']
        else:
            logger.warning(f'Unrecognized SNS notification type: {notification_type}')
            return None

        pairs = [f'{field}\n{self._notification.get(field)}' for field in fields]
        message = '\n'.join(pairs) + '\n'
        return bytes(message, 'utf-8')

    @staticmethod
    def get_keyfile(cert_url):
        """
        Function to acquire the keyfile

        SNS keys expire and Amazon does not promise they will use the same key
        for all SNS requests. So we need to keep a copy of the cert in our cache.
        """
        pem_data = cache.get(cert_url)
        if not pem_data:
            try:
                pem_data = requests.get(cert_url).content
            except OSError:
                logger.error(f'Unable to retrieve certificate, URL: {cert_url}')
                return None

            cache.set(cert_url, pem_data)

        return pem_data

    def get_notification(self):
        if not self._notification:
            _ = self.check_notification()
        return self._notification

    def get_message(self):
        if not self._message:
            _ = self.check_message()
        return self._message
