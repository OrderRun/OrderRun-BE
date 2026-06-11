from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.api.v1.notifications import get_notification_dispatcher
from app.main import app
from app.models.notification import Notification, NotificationStatus, NotificationType


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RecordingNotificationDispatcher:
    def send_custom_notification(
        self,
        db,
        user_id: str,
        title: str,
        body: str,
        data=None,
        related_entity_type=None,
        related_entity_id=None,
        image=None,
    ) -> Notification:
        _ = image
        notification = Notification(
            user_id=user_id,
            notification_type=NotificationType.CUSTOM,
            title=title,
            body=body,
            data='{"proposalId":1}' if data else None,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            status=NotificationStatus.SENT,
            fcm_message_id="projects/orderrun/messages/1",
            sent_at=utcnow_naive(),
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification


def test_root_response_matches_openapi_example(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


def test_notification_list_stats_detail_and_mark_read(client, db, factory, auth_headers, sample_user):
    unread = factory.notification(sample_user.id)
    factory.notification(
        sample_user.id,
        status=NotificationStatus.READ,
        read_at=utcnow_naive(),
    )
    factory.notification(
        sample_user.id,
        status=NotificationStatus.FAILED,
        error_message="No FCM token",
    )

    listed = client.get("/api/v1/notifications", headers=auth_headers)
    stats = client.get("/api/v1/notifications/stats/me", headers=auth_headers)
    detail = client.get(f"/api/v1/notifications/{unread.id}", headers=auth_headers)
    marked = client.post(
        "/api/v1/notifications/mark-read",
        headers=auth_headers,
        json={"notification_ids": [unread.id]},
    )

    assert listed.status_code == 200
    assert listed.json()["success"] is True
    assert listed.json()["message"] == "Success"
    assert listed.json()["data"]["total"] == 3
    assert stats.status_code == 200
    assert stats.json()["success"] is True
    assert stats.json()["message"] == "Success"
    assert stats.json()["data"]["total_notifications"] == 3
    assert detail.status_code == 200
    assert detail.json()["success"] is True
    assert detail.json()["message"] == "Success"
    assert detail.json()["data"]["id"] == unread.id
    assert marked.status_code == 200
    assert marked.json()["success"] is True
    assert marked.json()["message"] == "1 notification(s) marked as read"
    assert marked.json()["data"]["marked_count"] == 1


def test_notification_list_filters_pages_and_isolates_users(client, factory, auth_headers, sample_user):
    other_user = factory.user(phone="01088880000", name="Other User")
    now = utcnow_naive()
    read = factory.notification(
        sample_user.id,
        status=NotificationStatus.READ,
        read_at=utcnow_naive(),
        created_at=now,
    )
    unread = factory.notification(sample_user.id, created_at=now + timedelta(seconds=1))
    factory.notification(other_user.id, created_at=now + timedelta(seconds=2))

    listed = client.get("/api/v1/notifications?page=1&page_size=1", headers=auth_headers)
    unread_only = client.get("/api/v1/notifications?unread_only=true", headers=auth_headers)

    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 2
    assert listed.json()["data"]["page"] == 1
    assert listed.json()["data"]["page_size"] == 1
    assert len(listed.json()["data"]["notifications"]) == 1
    assert listed.json()["data"]["notifications"][0]["id"] == unread.id
    assert unread_only.status_code == 200
    assert unread_only.json()["data"]["total"] == 1
    assert unread_only.json()["data"]["notifications"][0]["id"] == unread.id
    assert read.id not in [item["id"] for item in unread_only.json()["data"]["notifications"]]


def test_notification_detail_and_mark_read_are_user_scoped(client, db, factory, auth_headers, sample_user):
    other_user = factory.user(phone="01077770000", name="Other User")
    other_notification = factory.notification(other_user.id)
    own_read = factory.notification(
        sample_user.id,
        status=NotificationStatus.READ,
        read_at=utcnow_naive(),
    )
    own_unread = factory.notification(sample_user.id)

    missing = client.get(f"/api/v1/notifications/{other_notification.id}", headers=auth_headers)
    marked = client.post(
        "/api/v1/notifications/mark-read",
        headers=auth_headers,
        json={"notification_ids": [other_notification.id, own_read.id, own_unread.id]},
    )

    db.refresh(other_notification)
    db.refresh(own_read)
    db.refresh(own_unread)

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "ERROR"
    assert marked.status_code == 200
    assert marked.json()["data"]["marked_count"] == 1
    assert other_notification.read_at is None
    assert own_read.status == NotificationStatus.READ
    assert own_unread.status == NotificationStatus.READ


def test_notification_send_and_failure_cases(client, db, auth_headers, sample_user):
    app.dependency_overrides[get_notification_dispatcher] = lambda: RecordingNotificationDispatcher()

    sent = client.post(
        "/api/v1/notifications/send",
        headers=auth_headers,
        json={
            "notification_type": "custom",
            "title": "테스트 알림",
            "body": "테스트 알림 본문입니다.",
            "data": {"proposalId": 1},
            "related_entity_type": "proposal",
            "related_entity_id": 1,
        },
    )
    missing = client.get("/api/v1/notifications/999999", headers=auth_headers)
    invalid_mark_read = client.post(
        "/api/v1/notifications/mark-read",
        headers=auth_headers,
        json={"notification_ids": []},
    )
    unauthenticated = client.get("/api/v1/notifications")

    app.dependency_overrides.pop(get_notification_dispatcher, None)

    assert sent.status_code == 201
    assert sent.json()["success"] is True
    assert sent.json()["message"] == "Success"
    assert sent.json()["data"]["title"] == "테스트 알림"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "ERROR"
    assert invalid_mark_read.status_code == 400
    assert invalid_mark_read.json()["error"]["code"] == "VALIDATION_ERROR"
    assert unauthenticated.status_code == 401
