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
| `status` | Enum | Required, Default=POSTED | 상태 |
| `created_at` | DateTime | Required | 생성 시각 |
| `updated_at` | DateTime | Required | 수정 시각 |

## 상태 정의

```python
class ProposalStatus(str, Enum):
    POSTED = "POSTED"      # 등록됨 (초기 상태)
    OFFERED = "OFFERED"    # 제안 접수됨
    MATCHED = "MATCHED"    # 매칭 완료
    CANCELLED = "CANCELLED" # 취소됨
```

## 상태 전이 규칙

| 현재 상태 | 이벤트 | 다음 상태 | 조건 |
|-----------|--------|-----------|------|
| POSTED | 첫 Offer 등록 | OFFERED | Offer 생성 시 |
| OFFERED | Offer 수락 | MATCHED | 유효한 Offer 존재 |
| POSTED/OFFERED | 취소 요청 | CANCELLED | 매칭 전에만 가능 |
| MATCHED | 취소 요청 | 거부 | 매칭 후에는 취소 불가 |

## 비즈니스 규칙

1. **생성 규칙**
   - 생성 시 상태는 항상 `POSTED`
   - 작성자는 인증된 사용자여야 함
   - 데드라인은 현재 시각보다 미래여야 함
   - 심부름비는 0 이상의 정수

2. **조회 규칙**
   - 모든 사용자가 전체 목록 조회 가능
   - 상세 조회도 모든 사용자 가능 (공개 정보)

3. **수정 규칙**
   - 작성자만 수정 가능
   - `POSTED` 상태에서만 수정 가능
   - `OFFERED`, `MATCHED` 상태에서는 수정 불가

4. **삭제/취소 규칙**
   - 작성자만 취소 가능
   - `MATCHED` 상태에서는 취소 불가
   - 취소 시 연관된 Offer들도 처리 필요

## 관계

- **User (1:N)**: 한 사용자가 여러 Proposal 작성 가능
- **Offer (1:N)**: 하나의 Proposal에 여러 Offer 가능
- **Mission (1:0..1)**: 수락된 Proposal만 Mission 생성

## 예시

```json
{
  "id": 1,
  "orderer_id": 10,
  "title": "강남역에서 커피 배달 부탁드립니다",
  "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다. 건물 입구에서 전달해주세요.",
  "deadline": "2026-03-27T15:00:00+09:00",
  "errand_fee": 5000,
  "status": "POSTED",
  "created_at": "2026-03-27T10:30:00+09:00",
  "updated_at": "2026-03-27T10:30:00+09:00"
}
```
