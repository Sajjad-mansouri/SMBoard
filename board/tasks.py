import logging
import smtplib
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
from celery import shared_task
from .models import Activity
from account.models import NotificationDelivery

import time

logger = logging.getLogger(__name__)
UserModel = get_user_model()

@shared_task(
    acks_late=True,
    autoretry_for=(smtplib.SMTPException, TimeoutError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5
    )
def send_email_task(**kwargs):

    try:
        activity = Activity.objects.get(id=kwargs.get("activity_id"))
        recipient = UserModel.objects.get(username=kwargs.get("recipient"))
    except (Activity.DoesNotExist, UserModel.DoesNotExist):
        logger.warning("Email task skipped.Activity or recipient missing.")
        return

    text_content = render_to_string("board/email/instant_notif.txt", kwargs)
    html_content = render_to_string("board/email/instant_notif.html", kwargs)

    email = EmailMultiAlternatives(
            subject=f"New activity in '{kwargs.get('board')}' board",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[kwargs.get("recipient_email")]
        )

    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


    NotificationDelivery.objects.get_or_create(
        activity=activity,
        recipient=recipient,
    )
    logger.info("Notification email sent to %s", kwargs.get("recipient_email"))
