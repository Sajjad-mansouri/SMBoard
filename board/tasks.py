import logging
import smtplib
from datetime import datetime, timedelta
from django.db import transaction
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from celery import shared_task, group
from .models import Activity
from account.models import Notification, NotificationDelivery

import time

logger = logging.getLogger(__name__)
UserModel = get_user_model()


def get_board_url(board_id):
    path = reverse("board:board_detail", kwargs={"pk":board_id})
    return f"{settings.SITE_DOMAIN}{path}"

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



@shared_task(
    acks_late=True,
    autoretry_for=(smtplib.SMTPException, TimeoutError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5
    )
def send_bulk_activity_email_task(recipient_id, recipient, recipient_email, days):
        try:
            recipient = UserModel.objects.get(id=recipient_id)
        except (Activity.DoesNotExist, UserModel.DoesNotExist):
            logger.warning("Email task skipped.Activity or recipient missing.")
            return

        now = timezone.now()
        q = Q(created__gte=now - timedelta(days=days))
        activities = Activity.objects.filter(q)
        activities = activities.exclude(activity_delivered_notifications__recipient=recipient_id).distinct()
        if activities:
            kwargs = {"activities":activities, "recipient":recipient,"workstation_link":settings.SITE_DOMAIN}
            text_content = render_to_string("board/email/periodically_notif.txt", kwargs)
            html_content = render_to_string("board/email/periodically_notif.html", kwargs)

            email = EmailMultiAlternatives(
                subject=f"New Activities",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
        with transaction.atomic():
            NotificationDelivery.objects.bulk_create(
                [
                    NotificationDelivery(
                        activity=activity,
                        recipient=recipient
                        )

                    for activity in activities

                ],
                ignore_conflicts=True

                )


@shared_task
def daily_notification():
    notifications = Notification.objects.filter(email_frequency="daily").select_related("user")

    job = group(
        send_bulk_activity_email_task.s(
                notification.user.id,
                notification.user.username,
                notification.user.email,
                days=1
            )
        for notification in notifications
        )

    job.delay()

@shared_task
def weekly_notification():
    notifications = Notification.objects.filter(email_frequency="weekly").select_related("user")

    job = group(
        send_bulk_activity_email_task.s(
                notification.user.id,
                notification.user.username,
                notification.user.email,
                days=7
            )
        for notification in notifications
        )

    job.delay()