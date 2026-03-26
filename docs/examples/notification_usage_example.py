"""
FCM Notification System Usage Examples

이 파일은 FCM 알림 시스템을 다양한 상황에서 사용하는 예제를 포함합니다.
"""

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.fcm_service import FCMService
from app.services.notification_dispatcher import NotificationDispatcher
from app.core.config import settings


# =============================================================================
# 예제 1: 의뢰(Proposal) 관련 알림
# =============================================================================

def example_proposal_workflow():
    """의뢰 생성부터 완료까지 알림 흐름"""

    router = APIRouter()

    @router.post("/proposals")
    def create_proposal(
        proposal_data: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        fcm_service: FCMService = Depends(lambda: FCMService(settings.fcm_credentials_path)),
    ):
        """
        새 의뢰 생성 API
        - 의뢰를 생성하고 주변 러너들에게 알림
        """
        dispatcher = NotificationDispatcher(fcm_service)

        # 1. 의뢰 생성 (비즈니스 로직)
        # proposal = create_proposal_in_db(db, proposal_data, current_user.id)

        # 2. 주변 러너에게 새 의뢰 알림 (예시)
        # nearby_runners = find_nearby_runners(db, proposal.location)
        # for runner in nearby_runners:
        #     dispatcher.send_custom_notification(
        #         db=db,
        #         user_id=runner.id,
        #         title="새로운 의뢰가 등록되었습니다!",
        #         body=f"{proposal.pickup_location}에서 {proposal.delivery_location}까지",
        #         related_entity_type="proposal",
        #         related_entity_id=proposal.id
        #     )

        return {"message": "Proposal created and notifications sent"}

    @router.post("/proposals/{proposal_id}/match/{runner_id}")
    def match_proposal_with_runner(
        proposal_id: int,
        runner_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        fcm_service: FCMService = Depends(lambda: FCMService(settings.fcm_credentials_path)),
    ):
        """
        의뢰와 러너 매칭 API
        - 의뢰자와 러너 모두에게 알림
        """
        dispatcher = NotificationDispatcher(fcm_service)

        # proposal = get_proposal(db, proposal_id)
        # if proposal.customer_id != current_user.id:
        #     raise HTTPException(status_code=403, detail="Not authorized")

        # 매칭 처리
        # match_proposal(db, proposal_id, runner_id)

        # 의뢰자와 러너에게 알림
        dispatcher.notify_proposal_matched(
            db=db,
            proposal_id=proposal_id,
            customer_id=current_user.id,  # proposal.customer_id
            runner_id=runner_id,
            proposal_title="강남역에서 홍대입구까지 배달"  # proposal.title
        )

        return {"message": "Matched and notifications sent"}


# =============================================================================
# 예제 2: 제안(Offer) 관련 알림
# =============================================================================

def example_offer_workflow():
    """제안 생성부터 수락/거절까지 알림 흐름"""

    router = APIRouter()

    @router.post("/offers")
    def create_offer(
        offer_data: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        fcm_service: FCMService = Depends(lambda: FCMService(settings.fcm_credentials_path)),
    ):
        """
        새 제안 생성 API
        - 러너가 의뢰에 제안하면 의뢰자에게 알림
        """
        dispatcher = NotificationDispatcher(fcm_service)

        # 제안 생성
        # proposal = get_proposal(db, offer_data["proposal_id"])
        # offer = create_offer_in_db(db, offer_data, current_user.id)

        # 의뢰자에게 새 제안 알림
        dispatcher.notify_offer_received(
            db=db,
            offer_id=1,  # offer.id
            proposal_id=offer_data["proposal_id"],
            customer_id=123,  # proposal.customer_id
            runner_id=current_user.id,
            proposal_title="배달 의뢰",  # proposal.title
            offer_amount=offer_data["amount"]
        )

        return {"message": "Offer created and notification sent"}

    @router.post("/offers/{offer_id}/accept")
    def accept_offer(
        offer_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        fcm_service: FCMService = Depends(lambda: FCMService(settings.fcm_credentials_path)),
    ):
        """
        제안 수락 API
        - 러너에게 수락 알림
        """
        dispatcher = NotificationDispatcher(fcm_service)

        # offer = get_offer(db, offer_id)
        # proposal = get_proposal(db, offer.proposal_id)

        # 제안 수락 처리
        # accept_offer_in_db(db, offer_id)

        # 러너에게 수락 알림
        dispatcher.notify_offer_accepted(
            db=db,
            offer_id=offer_id,
            proposal_id=1,  # offer.proposal_id
            runner_id=456,  # offer.runner_id
            proposal_title="배달 의뢰"  # proposal.title
        )

        return {"message": "Offer accepted and notification sent"}


# =============================================================================
# 예제 3: 미션(Mission) 관련 알림
# =============================================================================

def example_mission_workflow():
    """미션 시작부터 완료까지 알림 흐름"""

    router = APIRouter()

    @router.post("/missions/{mission_id}/start")
    def start_mission(
        mission_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        fcm_service: FCMService = Depends(lambda: FCMService(settings.fcm_credentials_path)),
    ):
        """
        미션 시작 API
        - 의뢰자와 러너에게 시작 알림
        """
        dispatcher = NotificationDispatcher(fcm_service)

        # mission = get_mission(db, mission_id)
        # start_mission_in_db(db, mission_id)

        # 시작 알림
        dispatcher.notify_mission_started(
            db=db,
            mission_id=mission_id,
            customer_id=123,  # mission.customer_id
            runner_id=current_user.id,
            mission_title="강남역 배달 미션"  # mission.title
        )

        return {"message": "Mission started and notifications sent"}

    @router.post("/missions/{mission_id}/complete")
    def complete_mission(
        mission_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        fcm_service: FCMService = Depends(lambda: FCMService(settings.fcm_credentials_path)),
    ):
        """
        미션 완료 API
        - 의뢰자와 러너에게 완료 알림
        """
        dispatcher = NotificationDispatcher(fcm_service)

        # mission = get_mission(db, mission_id)
        # complete_mission_in_db(db, mission_id)

        # 완료 알림
        dispatcher.notify_mission_completed(
            db=db,
            mission_id=mission_id,
            customer_id=123,  # mission.customer_id
            runner_id=current_user.id,
            mission_title="강남역 배달 미션"  # mission.title
        )

        return {"message": "Mission completed and notifications sent"}


# =============================================================================
# 예제 4: 결제(Payment) 관련 알림
# =============================================================================

def example_payment_workflow():
    """결제 완료/실패 알림"""

    router = APIRouter()

    @router.post("/payments/{payment_id}/process")
    def process_payment(
        payment_id: int,
        db: Session = Depends(get_db),
        fcm_service: FCMService = Depends(lambda: FCMService(settings.fcm_credentials_path)),
    ):
        """
        결제 처리 API
        - 결제 성공/실패에 따라 알림
        """
        dispatcher = NotificationDispatcher(fcm_service)

        # payment = get_payment(db, payment_id)
        # mission = get_mission(db, payment.mission_id)

        # 결제 처리
        # result = process_payment_external(payment)

        # if result.success:
        #     dispatcher.notify_payment_completed(
        #         db=db,
        #         payment_id=payment_id,
        #         user_id=payment.user_id,
        #         amount=payment.amount,
        #         mission_title=mission.title
        #     )
        # else:
        #     dispatcher.notify_payment_failed(
        #         db=db,
        #         payment_id=payment_id,
        #         user_id=payment.user_id,
        #         amount=payment.amount,
        #         mission_title=mission.title,
        #         reason=result.error_message
        #     )

        return {"message": "Payment processed and notification sent"}


# =============================================================================
# 예제 5: 시스템 공지
# =============================================================================

def example_system_announcement():
    """시스템 전체 공지"""

    router = APIRouter()

    @router.post("/admin/announcements")
    def send_announcement(
        announcement_data: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        fcm_service: FCMService = Depends(lambda: FCMService(settings.fcm_credentials_path)),
    ):
        """
        시스템 공지 API (관리자 전용)
        - 모든 활성 사용자 또는 특정 그룹에게 공지
        """
        # if current_user.role != "admin":
        #     raise HTTPException(status_code=403, detail="Admin only")

        dispatcher = NotificationDispatcher(fcm_service)

        # 특정 사용자 그룹 또는 전체 사용자
        # target_users = get_target_users(db, announcement_data.get("target_group"))
        target_user_ids = [1, 2, 3, 4, 5]  # 예시

        dispatcher.notify_system_announcement(
            db=db,
            user_ids=target_user_ids,
            title=announcement_data["title"],
            body=announcement_data["body"],
            data=announcement_data.get("data")
        )

        return {"message": f"Announcement sent to {len(target_user_ids)} users"}


# =============================================================================
# 예제 6: 커스텀 알림 (테스트용)
# =============================================================================

def example_custom_notification():
    """커스텀 알림 전송"""

    router = APIRouter()

    @router.post("/test/send-notification")
    def send_test_notification(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        fcm_service: FCMService = Depends(lambda: FCMService(settings.fcm_credentials_path)),
    ):
        """
        테스트용 커스텀 알림
        """
        dispatcher = NotificationDispatcher(fcm_service)

        dispatcher.send_custom_notification(
            db=db,
            user_id=current_user.id,
            title="테스트 알림",
            body="이것은 테스트 알림입니다.",
            data={
                "test_key": "test_value",
                "timestamp": "2024-01-15T10:30:00"
            },
            image="https://example.com/image.png"
        )

        return {"message": "Test notification sent"}


# =============================================================================
# 예제 7: FCM Service 직접 사용
# =============================================================================

def example_fcm_service_direct():
    """FCM Service를 직접 사용하는 고급 예제"""

    from app.models.notification import NotificationType

    def send_custom_fcm_notification(db: Session, user_id: int):
        """
        FCM Service를 직접 사용하여 더 세밀한 제어
        """
        fcm_service = FCMService(credentials_path=settings.fcm_credentials_path)

        # 단일 사용자에게 전송
        notification, results = fcm_service.send_to_user(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.CUSTOM,
            title="커스텀 알림",
            body="FCM Service를 직접 사용한 알림입니다.",
            data={
                "custom_field_1": "value1",
                "custom_field_2": "value2"
            },
            image="https://example.com/notification-image.png"
        )

        # 결과 확인
        print(f"Notification ID: {notification.id}")
        print(f"Status: {notification.status}")

        for idx, result in enumerate(results):
            if result.success:
                print(f"Device {idx}: Success - Message ID: {result.message_id}")
            else:
                print(f"Device {idx}: Failed - {result.error_code}: {result.error_message}")

                # 에러 타입별 처리
                if result.error_code == "UNREGISTERED":
                    # 토큰 비활성화 또는 삭제
                    pass
                elif result.error_code == "INVALID_ARGUMENT":
                    # 잘못된 인자 로깅
                    pass

        return notification

    def send_to_topic_example():
        """
        토픽 기반 브로드캐스트 (특정 주제를 구독한 모든 사용자)
        """
        fcm_service = FCMService(credentials_path=settings.fcm_credentials_path)

        result = fcm_service.send_to_topic(
            topic="all_runners",
            title="새로운 의뢰 알림",
            body="강남역 근처에 새로운 배달 의뢰가 등록되었습니다.",
            data={
                "proposal_id": "12345",
                "location": "gangnam"
            }
        )

        if result.success:
            print(f"Topic notification sent: {result.message_id}")
        else:
            print(f"Failed to send to topic: {result.error_message}")

    def send_multicast_example(db: Session):
        """
        여러 디바이스에 한 번에 전송
        """
        fcm_service = FCMService(credentials_path=settings.fcm_credentials_path)

        # 토큰 리스트 준비
        tokens = ["token1", "token2", "token3"]

        result = fcm_service.send_multicast(
            tokens=tokens,
            title="배치 알림",
            body="여러 디바이스에 동시 전송",
            data={"batch_id": "123"}
        )

        print(f"Success: {result['success_count']}/{len(tokens)}")
        print(f"Failed: {result['failure_count']}/{len(tokens)}")

        # 개별 결과 확인
        for response in result.get("responses", []):
            if response["success"]:
                print(f"Token {response['token']}: Success")
            else:
                print(f"Token {response['token']}: Failed - {response['error_code']}")


# =============================================================================
# 예제 8: 백그라운드 작업으로 알림 전송 (Celery/RQ)
# =============================================================================

def example_background_notification():
    """
    백그라운드 작업으로 알림 전송 (선택적)

    대량 알림이나 지연 전송이 필요한 경우 Celery나 RQ 같은
    백그라운드 작업 큐를 사용할 수 있습니다.
    """

    # Celery 예제 (설치 필요: pip install celery)
    # from celery import Celery
    #
    # celery_app = Celery('orderrun', broker='redis://localhost:6379/0')
    #
    # @celery_app.task
    # def send_notification_async(user_id: int, title: str, body: str):
    #     """백그라운드로 알림 전송"""
    #     from app.core.database import SessionLocal
    #     from app.services.fcm_service import FCMService
    #     from app.services.notification_dispatcher import NotificationDispatcher
    #
    #     db = SessionLocal()
    #     try:
    #         fcm_service = FCMService(credentials_path=settings.fcm_credentials_path)
    #         dispatcher = NotificationDispatcher(fcm_service)
    #
    #         dispatcher.send_custom_notification(
    #             db=db,
    #             user_id=user_id,
    #             title=title,
    #             body=body
    #         )
    #     finally:
    #         db.close()
    #
    # # 사용
    # send_notification_async.delay(user_id=123, title="Test", body="Async notification")

    pass


# =============================================================================
# 예제 9: 알림 스케줄링 (예약 알림)
# =============================================================================

def example_scheduled_notification():
    """
    예약 알림 (특정 시간에 전송)

    APScheduler 같은 스케줄러를 사용하여 구현 가능
    """

    # from apscheduler.schedulers.background import BackgroundScheduler
    # from datetime import datetime, timedelta
    #
    # scheduler = BackgroundScheduler()
    #
    # def send_scheduled_notification(user_id: int, message: str):
    #     """예약된 시간에 알림 전송"""
    #     from app.core.database import SessionLocal
    #     # ... 알림 전송 로직
    #     pass
    #
    # # 1시간 후 알림 예약
    # run_time = datetime.now() + timedelta(hours=1)
    # scheduler.add_job(
    #     send_scheduled_notification,
    #     'date',
    #     run_date=run_time,
    #     args=[123, "1시간 후 알림"]
    # )
    #
    # scheduler.start()

    pass


# =============================================================================
# 예제 10: 알림 통계 및 분석
# =============================================================================

def example_notification_analytics():
    """알림 통계 조회"""

    from sqlalchemy import func
    from app.models.notification import Notification, NotificationStatus, NotificationType

    def get_notification_stats(db: Session, user_id: int):
        """사용자별 알림 통계"""
        stats = db.query(
            NotificationStatus,
            func.count(Notification.id).label('count')
        ).filter(
            Notification.user_id == user_id
        ).group_by(
            NotificationStatus
        ).all()

        return {status.value: count for status, count in stats}

    def get_notification_stats_by_type(db: Session, user_id: int):
        """알림 타입별 통계"""
        stats = db.query(
            NotificationType,
            func.count(Notification.id).label('count')
        ).filter(
            Notification.user_id == user_id
        ).group_by(
            NotificationType
        ).all()

        return {ntype.value: count for ntype, count in stats}

    def get_delivery_success_rate(db: Session, user_id: int):
        """알림 전송 성공률"""
        total = db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id
        ).scalar()

        successful = db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id,
            Notification.status.in_([NotificationStatus.SENT, NotificationStatus.DELIVERED, NotificationStatus.READ])
        ).scalar()

        if total == 0:
            return 0.0

        return (successful / total) * 100
