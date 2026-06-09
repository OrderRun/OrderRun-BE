# Terms Agreement Model

## 범위

- `terms_agreements`
- `TermsType`

## 1. `terms_agreements`

### 테이블 정보

- 테이블명: `terms_agreements`
- 설명: 사용자별 최신 필수 약관 동의 상태

### 속성

| 필드명 | 데이터 타입 | Null 허용 | 설명 |
|--------|------------|----------|------|
| `id` | BIGINT | NO | 기본키, auto increment |
| `user_id` | VARCHAR(36) | NO | 사용자 ID |
| `terms_of_service` | BOOLEAN | NO | 이용약관 동의 여부 |
| `privacy_policy` | BOOLEAN | NO | 개인정보처리방침 동의 여부 |
| `payment_refund_policy` | BOOLEAN | NO | 결제/환불지급정책 동의 여부 |
| `agreed_at` | DATETIME(6) | NO | 약관 동의 시각 |
| `created_at` | DATETIME(6) | NO | 생성 시각 |
| `updated_at` | DATETIME(6) | NO | 수정 시각 |

### 제약조건

- Primary key: `id`
- Foreign key: 없음
- Unique constraints:
  - `uk_terms_agreements_user_id` on `user_id`
- Indexes:
  - `idx_terms_agreements_user_id` on `user_id`
- Check constraints: 없음

### 비즈니스 검증 규칙

- `user_id`는 반드시 존재하는 사용자 ID여야 하며, DB FK가 아니라 애플리케이션 레벨에서 검증한다.
- 사용자당 동의 row는 1건만 유지한다.
- 같은 사용자가 다시 동의하면 새 row를 만들지 않고 기존 row를 갱신한다.
- 세 약관 필드는 모두 필수이고 `true`여야 한다.
- `agreed_at`은 요청 처리 시점의 UTC 현재 시각이다.

### 관계

- User: N:1 매핑처럼 조회할 수 있으나 `user_id` unique 제약 때문에 실질적으로 사용자당 1건이다.
- DB FK constraint는 두지 않는다.

## 2. `TermsType`

### Enum 항목

| Enum | 약관 이름 | 필수 |
|------|-----------|------|
| `TERMS_OF_SERVICE` | 이용약관 | O |
| `PRIVACY_POLICY` | 개인정보처리방침 | O |
| `PAYMENT_REFUND_POLICY` | 결제/환불지급정책 | O |

### 규칙

- 필수 여부는 enum의 `required` 속성으로 관리한다.
- 서비스는 요청 필드를 직접 하드코딩해서만 검사하지 않고, `TermsType`의 필수 항목을 기준으로 검증한다.
- 선택 약관과 버전 관리는 현재 범위에 포함하지 않는다.
