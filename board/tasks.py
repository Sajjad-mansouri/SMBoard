import logging
import smtplib
from datetime import timedelta

from celery import group, shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Q
from django.forms.models import model_to_dict
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from account.models import Notification, NotificationDelivery

from .models import Activity

logger = logging.getLogger(__name__)
UserModel = get_user_model()


def get_board_url(board_id):
    path = reverse("board:board_detail", kwargs={"pk": board_id})
    return f"{settings.SITE_DOMAIN}{path}"


@shared_task(
    acks_late=True,
    autoretry_for=(smtplib.SMTPException, TimeoutError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def send_email_task(**kwargs):
    try:
        recipient_id = kwargs.get("recipient_id")
        q = (
            Q(board__board_memberships__user_id=recipient_id)
            & Q(id=kwargs.get("activity_id"))
        ) & ~Q(user_id=recipient_id)
        activity = Activity.objects.get(q)
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
        to=[kwargs.get("recipient_email")],
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
    max_retries=5,
)
def send_bulk_activity_email_task(recipient_id, recipient, recipient_email, days):
    try:
        recipient = UserModel.objects.get(id=recipient_id)
    except (Activity.DoesNotExist, UserModel.DoesNotExist):
        logger.warning("Email task skipped.Activity or recipient missing.")
        return

    now = timezone.now()
    recipient.user_activities.values_list("action_type", flat=True).distinct()
    user_notificaiton = model_to_dict(recipient.notification)
    enabled_notification = [
        key for key, value in user_notificaiton.items() if value is True
    ]

    q = (
        Q(created__gte=now - timedelta(days=days))
        & Q(board__board_memberships__user_id=recipient_id)
        & Q(action_type__in=enabled_notification)
    ) & ~Q(user_id=recipient_id)
    activities = Activity.objects.filter(q)
    activities = activities.exclude(
        activity_delivered_notifications__recipient=recipient_id
    ).distinct()
    if activities:
        kwargs = {
            "activities": activities,
            "recipient": recipient,
            "site_address": settings.SITE_ADDRESS,
        }
        text_content = render_to_string("board/email/periodically_notif.txt", kwargs)
        html_content = render_to_string("board/email/periodically_notif.html", kwargs)

        email = EmailMultiAlternatives(
            subject="New Activities",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
    with transaction.atomic():
        NotificationDelivery.objects.bulk_create(
            [
                NotificationDelivery(activity=activity, recipient=recipient)
                for activity in activities
            ],
            ignore_conflicts=True,
        )


@shared_task
def daily_notification():
    notifications = Notification.objects.filter(email_frequency="daily").select_related(
        "user"
    )
    signatures = [
        send_bulk_activity_email_task.s(
            notification.user.id,
            notification.user.username,
            notification.user.email,
            days=1,
        )
        for notification in notifications
    ]
    job = group(signatures)

    job.delay()


@shared_task
def weekly_notification():
    notifications = Notification.objects.filter(
        email_frequency="weekly"
    ).select_related("user")
    signatures = [
        send_bulk_activity_email_task.s(
            notification.user.id,
            notification.user.username,
            notification.user.email,
            days=7,
        )
        for notification in notifications
    ]
    job = group(signatures)

    job.delay()
