# 회원 탈퇴 정책

회원 탈퇴 시 개인정보와 인증·연락 수단은 즉시 hard delete한다. 거래 이력의 참조 무결성을 위해 `users` row와 비식별 활동 기록만 유지하며, 로그인과 일반 API 접근은 즉시 차단한다.

## 기본 원칙

- `users` row는 삭제하지 않고 `deleted = true`, `deleted_at = now`로 표시한다.
- 사용자 이름, 전화번호, 전화번호 인증 시각, 마지막 로그인 시각, 비밀번호 해시, 알림 설정은 `null`로 영구 삭제한다.
- 탈퇴 사용자의 이름은 저장하지 않고, 활동 조회 응답에서만 `탈퇴한 사용자`로 표시한다.
- 탈퇴 후 같은 전화번호 재가입은 허용한다.
- Proposal, Offer, DisputeEvidence 같은 거래 활동 기록은 삭제하지 않는다.
- 탈퇴 사유 선택 이력은 개인정보 삭제와 별도로 `user_withdrawals`에 보존한다.

## 탈퇴 불가 상태

이미 매칭되었거나 분쟁/완료 확인 흐름이 남아 있는 활동이 있으면 탈퇴할 수 없다. UI의 "진행 중인 임무"는 현재 도메인에서 매칭 이후 수행, 완료 확인, 분쟁 단계의 Proposal/Offer를 의미한다.

Proposal 기준:

- `MATCHED`
- `ORDER_COMPLETED`
- `DISPUTED`

Offer 기준:

- `ACCEPTED`
- `RUNNER_COMPLETED`
- `DISPUTED`

이 상태는 상대방 거래 경험, 고객센터 대응, 분쟁 처리, 정산 확인이 남을 수 있으므로 탈퇴 요청을 `USER_WITHDRAWAL_BLOCKED`로 차단한다.

## 탈퇴 시 자동 취소 상태

아직 매칭 전인 활동은 탈퇴를 막지 않고 자동 취소한다. 이 상태는 상대방과 거래가 확정되기 전이므로 탈퇴 요청 트랜잭션 안에서 종료 상태로 전환한다.

Proposal 기준:

- `HOLDING`
- `POSTED`
- `OFFERED`

Offer 기준:

- `WAITING`

사용자가 작성한 Proposal이 자동 취소될 때 해당 Proposal에 연결된 대기 Offer도 `CANCELLED` 처리한다.

## 탈퇴 가능 상태

모든 활동이 종료 상태라면 탈퇴를 허용한다.

Proposal 기준:

- `ALL_COMPLETED`
- `RESOLVED`
- `CANCELLED`

Offer 기준:

- `ALL_COMPLETED`
- `RESOLVED`
- `REJECTED`
- `CANCELLED`

탈퇴가 허용되어도 사용자 row는 hard delete하지 않는다.

## 즉시 정리 데이터

탈퇴 직후 즉시 삭제한다.

- `user_fcm_tokens`
- 탈퇴 사용자 전화번호 기준 `auth_phone_verifications`
- `settlement_accounts`
- `notifications`

`settlement_accounts`는 미결 정산 트랜잭션이 아니라 정산 계좌 개인정보로 취급한다.

## 보존 데이터

즉시 삭제하지 않는다.

- `users` soft-deleted row
- `user_withdrawals`
- `proposals`
- `offers`
- `dispute_evidences`
- `terms_agreements`

## 정산/결제 미결 검증

현재 코드에는 미결 정산/결제 트랜잭션을 표현하는 `payments` ORM이 없다. 따라서 현재 차단 검증은 Proposal/Offer의 수행·분쟁 상태를 기준으로 한다.

`payments` ORM과 정산 상태 전이가 도입되면 `PENDING`, `PROCESSING`, 환불/분쟁 처리 중 상태의 결제 또는 정산 row가 있는 사용자는 `USER_WITHDRAWAL_BLOCKED`로 차단한다.

## 탈퇴 사유

`GET /v1/user/withdrawal-reasons`는 활성 탈퇴 사유를 표시 순서대로 반환한다.

기본 탈퇴 사유:

- 원하는 임무가 많지 않았어요.
- 원하는 꼬봉(또는 행님)을 만나기 어려웠어요.
- 이용 방법이 어려웠어요.
- 앱이 자주 오류가 났어요.
- 다른 회원과 문제가 있었어요.
- 다른 서비스를 이용하려고 해요.
- 기타

`DELETE /v1/user`는 `reasonQuestionId`, `detailReason`을 선택 입력으로 받을 수 있다. `reasonQuestionId`가 활성 사유가 아니면 `VALIDATION_ERROR`를 반환한다. 사유의 `requires_detail`이 `true`이면 `detailReason`을 필수로 요구한다.

## API 공개 상태

`GET /v1/user/withdrawal-reasons`는 인증된 사용자에게 탈퇴 사유 목록을 제공한다.

`DELETE /v1/user`는 인증된 사용자의 탈퇴 요청을 처리한다.
