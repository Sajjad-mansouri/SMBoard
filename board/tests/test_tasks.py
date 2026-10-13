from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone

from account.models import NotificationDelivery
from api.tests.conftest import (
    ActivityFactory,
    BoardFactory,
    BoardMembershipFactory,
    NotificationDeliveryFactory,
    NotificationFactory,
    UserFactory,
)
from board.tasks import (
    daily_notification,
    send_bulk_activity_email_task,
    send_email_task,
    weekly_notification,
)


@pytest.mark.django_db
class TestSendEmailTask:
    """Tests for send_email_task."""

    @pytest.fixture
    def actor(self):
        return UserFactory(username="actor")

    @pytest.fixture
    def recipient(self):
        return UserFactory(
            username="recipient",
            email="recipient@example.com",
        )

    @pytest.fixture
    def board(self, actor):
        return BoardFactory(
            owner=actor,
            name="Development Board",
        )

    @pytest.fixture
    def membership(self, board, recipient):
        return BoardMembershipFactory(
            board=board,
            user=recipient,
            accepted=True,
        )

    @pytest.fixture
    def activity(self, actor, board):
        return ActivityFactory(
            board=board,
            user=actor,
        )

    @pytest.fixture
    def kwargs(
        self,
        recipient,
        board,
        activity,
        membership,
    ):
        return {
            "recipient": recipient.username,
            "recipient_id": recipient.id,
            "recipient_email": recipient.email,
            "activity_id": activity.id,
            "board": board.name,
        }

    # ------------------------------------------------------------------
    # Success
    # ------------------------------------------------------------------

    def test_send_email_successfully(
        self,
        kwargs,
        recipient,
        activity,
    ):
        send_email_task(**kwargs)

        assert len(mail.outbox) == 1

        email = mail.outbox[0]

        assert email.to == [recipient.email]
        assert email.subject == f"New activity in '{kwargs['board']}' board"

        assert email.body
        assert len(email.alternatives) == 1
        assert email.alternatives[0].mimetype == "text/html"

        assert NotificationDelivery.objects.filter(
            activity=activity,
            recipient=recipient,
        ).exists()

    # ------------------------------------------------------------------
    # Missing activity
    # ------------------------------------------------------------------

    def test_missing_activity_skips_task(
        self,
        kwargs,
    ):
        kwargs["activity_id"] = 999999

        send_email_task(**kwargs)

        assert len(mail.outbox) == 0
        assert NotificationDelivery.objects.count() == 0

    # ------------------------------------------------------------------
    # Missing recipient
    # ------------------------------------------------------------------

    def test_missing_recipient_skips_task(
        self,
        kwargs,
    ):
        kwargs["recipient"] = "unknown-user"

        send_email_task(**kwargs)

        assert len(mail.outbox) == 0
        assert NotificationDelivery.objects.count() == 0

    # ------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------

    def test_notification_delivery_is_not_duplicated(
        self,
        kwargs,
        recipient,
        activity,
    ):
        send_email_task(**kwargs)
        send_email_task(**kwargs)

        assert len(mail.outbox) == 2

        assert (
            NotificationDelivery.objects.filter(
                activity=activity,
                recipient=recipient,
            ).count()
            == 1
        )


@pytest.mark.django_db
class TestDailyNotificationTask:
    @patch("board.tasks.group")
    @patch("board.tasks.send_bulk_activity_email_task")
    def test_daily_notification_dispatches_one_task_per_user(
        self,
        mock_task,
        mock_group,
    ):
        user1 = UserFactory(email="u1@test.com")
        user2 = UserFactory(email="u2@test.com")

        NotificationFactory(
            user=user1,
            email_frequency="daily",
        )

        NotificationFactory(
            user=user2,
            email_frequency="daily",
        )

        daily_notification()

        assert mock_task.s.call_count == 2

        mock_task.s.assert_any_call(
            user1.id,
            user1.username,
            user1.email,
            days=1,
        )

        mock_task.s.assert_any_call(
            user2.id,
            user2.username,
            user2.email,
            days=1,
        )
        mock_group.return_value.delay.assert_called_once()


@pytest.mark.django_db
class TestWeeklyNotificationTask:
    @patch("board.tasks.group")
    @patch("board.tasks.send_bulk_activity_email_task")
    def test_weekly_notification_dispatches_tasks(
        self,
        mock_task,
        mock_group,
    ):
        user = UserFactory()

        NotificationFactory(
            user=user,
            email_frequency="weekly",
        )

        weekly_notification()

        mock_task.s.assert_called_once_with(
            user.id,
            user.username,
            user.email,
            days=7,
        )

        mock_group.return_value.delay.assert_called_once()


@pytest.mark.django_db
class TestSendBulkActivityEmailTask:
    @pytest.fixture
    def actor(self):
        return UserFactory()

    @pytest.fixture
    def recipient(self):
        return UserFactory(
            username="recipient",
            email="recipient@example.com",
        )

    @pytest.fixture
    def notification(self, recipient):
        return NotificationFactory(user=recipient)

    @pytest.fixture
    def board(self, actor):
        return BoardFactory(owner=actor)

    @pytest.fixture
    def membership(self, board, recipient):
        return BoardMembershipFactory(
            board=board,
            user=recipient,
            accepted=True,
        )

    @pytest.fixture
    def kwargs(self, recipient):
        return {
            "recipient_id": recipient.id,
            "recipient": recipient.username,
            "recipient_email": recipient.email,
            "days": 1,
        }

    def test_send_email_successfully(
        self,
        actor,
        notification,
        recipient,
        board,
        membership,
        kwargs,
    ):
        recipient.notification.add_comment = True
        recipient.notification.save(update_fields=["add_comment"])

        activity = ActivityFactory(
            board=board,
            user=actor,
            action_type="add_comment",
        )

        send_bulk_activity_email_task(**kwargs)

        assert len(mail.outbox) == 1

        email = mail.outbox[0]

        assert email.subject == "New Activities"
        assert email.to == [recipient.email]
        assert len(email.alternatives) == 1

        assert NotificationDelivery.objects.filter(
            activity=activity,
            recipient=recipient,
        ).exists()

    def test_missing_recipient_returns(
        self,
        kwargs,
    ):
        kwargs["recipient_id"] = 999999

        send_bulk_activity_email_task(**kwargs)

        assert len(mail.outbox) == 0
        assert NotificationDelivery.objects.count() == 0

    def test_no_matching_activity(
        self,
        recipient,
        notification,
        kwargs,
    ):
        recipient.notification.add_comment = True
        recipient.notification.save(update_fields=["add_comment"])

        send_bulk_activity_email_task(**kwargs)

        assert len(mail.outbox) == 0
        assert NotificationDelivery.objects.count() == 0

    def test_old_activity_is_ignored(
        self,
        actor,
        recipient,
        notification,
        board,
        membership,
        kwargs,
    ):
        recipient.notification.add_comment = True
        recipient.notification.save(update_fields=["add_comment"])

        activity = ActivityFactory(
            board=board,
            user=actor,
            action_type="comment_card",
        )

        activity.created = timezone.now() - timedelta(days=10)
        activity.save(update_fields=["created"])

        send_bulk_activity_email_task(**kwargs)

        assert len(mail.outbox) == 0

    def test_self_activity_is_not_sent(
        self,
        recipient,
        notification,
        board,
        membership,
        kwargs,
    ):
        recipient.notification.add_comment = True
        recipient.notification.save(update_fields=["add_comment"])

        ActivityFactory(
            board=board,
            user=recipient,
            action_type="add_comment",
        )

        send_bulk_activity_email_task(**kwargs)

        assert len(mail.outbox) == 0

    def test_disabled_notification_type(
        self,
        actor,
        recipient,
        notification,
        board,
        membership,
        kwargs,
    ):
        ActivityFactory(
            board=board,
            user=actor,
            action_type="add_comment",
        )

        send_bulk_activity_email_task(**kwargs)

        assert len(mail.outbox) == 0

    def test_already_delivered_activity(
        self,
        actor,
        recipient,
        notification,
        board,
        membership,
        kwargs,
    ):
        recipient.notification.add_comment = True
        recipient.notification.save(update_fields=["add_comment"])

        activity = ActivityFactory(
            board=board,
            user=actor,
            action_type="add_comment",
        )

        NotificationDeliveryFactory(
            activity=activity,
            recipient=recipient,
        )

        send_bulk_activity_email_task(**kwargs)

        assert len(mail.outbox) == 0

        assert (
            NotificationDelivery.objects.filter(
                activity=activity,
                recipient=recipient,
            ).count()
            == 1
        )

    def test_multiple_activities(
        self,
        actor,
        recipient,
        notification,
        board,
        membership,
        kwargs,
    ):
        recipient.notification.add_comment = True
        recipient.notification.save(update_fields=["add_comment"])

        activities = ActivityFactory.create_batch(
            3,
            board=board,
            user=actor,
            action_type="add_comment",
        )

        send_bulk_activity_email_task(**kwargs)

        assert len(mail.outbox) == 1

        assert NotificationDelivery.objects.filter(
            recipient=recipient,
        ).count() == len(activities)

    def test_task_is_idempotent(
        self,
        actor,
        recipient,
        notification,
        board,
        membership,
        kwargs,
    ):
        recipient.notification.add_comment = True
        recipient.notification.save(update_fields=["add_comment"])

        activity = ActivityFactory(
            board=board,
            user=actor,
            action_type="add_comment",
        )

        send_bulk_activity_email_task(**kwargs)
        send_bulk_activity_email_task(**kwargs)

        assert (
            NotificationDelivery.objects.filter(
                activity=activity,
                recipient=recipient,
            ).count()
            == 1
        )

        assert len(mail.outbox) == 1
