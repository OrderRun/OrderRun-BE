# Proposal Entity

## 개요
Proposal은 사용자가 심부름을 요청하는 핵심 엔티티입니다. 요청서를 작성하고, 러너들이 제안(Offer)을 제출하며, 하나가 수락되어 미션(Mission)으로 전환되는 생명주기를 가집니다.

## 필드 정의

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | BigInteger | PK, Auto-increment | 제안 고유 식별자 |
| `orderer_id` | BigInteger | FK(User), Required | 작성자 ID |
| `title` | String(50) | Required, 1-50자 | 제목 |
| `content` | String(500) | Required, 1-500자 | 내용 |
| `deadline` | DateTime | Required, 미래 시각 | 완료 희망 시각 |
| `errand_fee` | Integer | Required, >= 0 | 심부름비 (원 단위) |
| `status` | Enum | Required, Default=PENDING_PAYMENT | 상태 |
| `payment_status` | String(20) | Required, Default=PENDING | 입금 상태 (PENDING, CONFIRMED) |
| `payment_deadline` | DateTime | Required | 입금 마감 시각 (생성시각 + 24시간) |
| `depositor_name` | String(50) | Optional | 입금자명 |
| `payment_confirmed_at` | DateTime | Optional | 입금 확인 시각 |
| `payment_confirmed_by` | BigInteger | FK(User), Optional | 입금 확인한 관리자 ID |
| `created_at` | DateTime | Required | 생성 시각 |
| `updated_at` | DateTime | Required | 수정 시각 |

## 상태 정의

```python
class ProposalStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"  # 입금 대기 (초기 상태, 공개 전)
    POSTED = "POSTED"                     # 등록됨 (입금 완료 후 공개)
    OFFERED = "OFFERED"                   # 제안 접수됨
    MATCHED = "MATCHED"                   # 매칭 완료
    CANCELLED = "CANCELLED"               # 취소됨
```

## 상태 전이 규칙

| 현재 상태 | 이벤트 | 다음 상태 | 조건 |
|-----------|--------|-----------|------|
| PENDING_PAYMENT | 관리자 입금 확인 | POSTED | 24시간 내 입금 확인 |
| PENDING_PAYMENT | 24시간 경과 | 자동 삭제 | 입금 미확인 시 |
| POSTED | 첫 Offer 등록 | OFFERED | Offer 생성 시 |
| OFFERED | Offer 수락 | MATCHED | 유효한 Offer 존재 |
| POSTED/OFFERED | 취소 요청 | CANCELLED | 매칭 전에만 가능 |
| MATCHED | 취소 요청 | 거부 | 매칭 후에는 취소 불가 |

## 비즈니스 규칙

1. **생성 규칙**
   - 생성 시 상태는 항상 `PENDING_PAYMENT`
   - 작성자는 인증된 사용자여야 함
   - 데드라인은 현재 시각보다 미래여야 함
   - 심부름비는 0 이상의 정수
   - `payment_deadline`은 생성 시각 + 24시간으로 자동 설정
   - `payment_status`는 기본값 `PENDING`

2. **입금 규칙**
   - 오더러는 생성 후 시스템 계좌에 심부름비를 입금해야 함
   - 입금 계좌 정보는 시스템 설정(config)에서 관리
   - 24시간 내 입금하지 않으면 자동 삭제
   - 관리자가 입금을 확인하면 `POSTED` 상태로 전환
   - 입금 확인 시 `payment_status`를 `CONFIRMED`로 변경

3. **조회 규칙**
   - `PENDING_PAYMENT` 상태는 작성자와 관리자만 조회 가능
   - 일반 사용자(러너)는 `POSTED` 이상 상태만 조회 가능
   - 전체 목록 조회 시 `PENDING_PAYMENT` 자동 필터링
   - 작성자는 본인의 `PENDING_PAYMENT` 상태 조회 가능

4. **수정 규칙**
   - 작성자만 수정 가능
   - `PENDING_PAYMENT`, `POSTED` 상태에서만 수정 가능
   - `OFFERED`, `MATCHED` 상태에서는 수정 불가

5. **삭제/취소 규칙**
   - 작성자만 취소 가능
   - `MATCHED` 상태에서는 취소 불가
   - 취소 시 연관된 Offer들도 처리 필요
   - `PENDING_PAYMENT` 상태에서 24시간 경과 시 자동 삭제

## 관계

- **User (1:N)**: 한 사용자가 여러 Proposal 작성 가능
- **Offer (1:N)**: 하나의 Proposal에 여러 Offer 가능
- **Mission (1:0..1)**: 수락된 Proposal만 Mission 생성

## 예시

### 1. 생성 직후 (입금 대기 중)
```json
{
  "id": 1,
  "orderer_id": 10,
  "title": "강남역에서 커피 배달 부탁드립니다",
  "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다. 건물 입구에서 전달해주세요.",
  "deadline": "2026-03-27T15:00:00+09:00",
  "errand_fee": 5000,
  "status": "PENDING_PAYMENT",
  "payment_status": "PENDING",
  "payment_deadline": "2026-03-28T10:30:00+09:00",
  "depositor_name": null,
  "payment_confirmed_at": null,
  "payment_confirmed_by": null,
  "created_at": "2026-03-27T10:30:00+09:00",
  "updated_at": "2026-03-27T10:30:00+09:00"
}
```

### 2. 입금 확인 후 (공개됨)
```json
{
  "id": 1,
  "orderer_id": 10,
  "title": "강남역에서 커피 배달 부탁드립니다",
  "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다. 건물 입구에서 전달해주세요.",
  "deadline": "2026-03-27T15:00:00+09:00",
  "errand_fee": 5000,
  "status": "POSTED",
  "payment_status": "CONFIRMED",
  "payment_deadline": "2026-03-28T10:30:00+09:00",
  "depositor_name": "홍길동",
  "payment_confirmed_at": "2026-03-27T12:00:00+09:00",
  "payment_confirmed_by": 1,
  "created_at": "2026-03-27T10:30:00+09:00",
  "updated_at": "2026-03-27T12:00:00+09:00"
}
```
