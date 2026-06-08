from __future__ import annotations

from datetime import datetime

from app.api.v1.notifications import get_notification_dispatcher
from app.main import app
from app.models.notification import Notification, NotificationStatus, NotificationType


def make_notification(db, user_id: str, **overrides) -> Notification:
    values = {
        "user_id": user_id,
        "notification_type": NotificationType.CUSTOM,
        "title": "테스트 알림",
        "body": "테스트 알림 본문입니다.",
        "data": '{"proposalId":1}',
        "related_entity_type": "proposal",
        "related_entity_id": 1,
        "status": NotificationStatus.SENT,
        "fcm_message_id": "projects/orderrun/messages/1",
        "sent_at": datetime.utcnow(),
    }
    values.update(overrides)
    notification = Notification(**values)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


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
    ) -> None:
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
            sent_at=datetime.utcnow(),
        )
        db.add(notification)
        db.commit()


def test_root_response_matches_openapi_example(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


def test_notification_list_stats_detail_and_mark_read(client, db, auth_headers, sample_user):
    unread = make_notification(db, sample_user.id)
    make_notification(
        db,
        sample_user.id,
        status=NotificationStatus.READ,
        read_at=datetime.utcnow(),
    )
    make_notification(
        db,
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
    assert listed.json()["total"] == 3
    assert stats.status_code == 200
    assert stats.json()["total_notifications"] == 3
    assert detail.status_code == 200
    assert detail.json()["id"] == unread.id
    assert marked.status_code == 200
    assert marked.json()["marked_count"] == 1


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
    assert sent.json()["title"] == "테스트 알림"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "ERROR"
    assert invalid_mark_read.status_code == 400
    assert invalid_mark_read.json()["error"]["code"] == "VALIDATION_ERROR"
    assert unauthenticated.status_code == 401
