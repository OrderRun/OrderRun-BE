# API 라우터 구성 원칙

## 결정

`app/api/v1`의 라우터는 도메인별 패키지에 배치하고 모듈 이름을
`*_router.py`로 끝낸다. 파일 경로만 보아도 도메인과 HTTP 라우터 책임을
함께 식별할 수 있어야 한다.

`app/api/v1/router.py`는 v1 라우터의 유일한 조립 지점이다. 공통 `/v1`
prefix를 소유하며, `app/main.py`는 이 조립 라우터만 등록한다. 하위
라우터는 자신의 도메인 경로만 소유한다.

## 도메인 경계

- `user_auth`: 인증과 사용자 프로필
- `proposal`: 요청과 요청 신고 사유
- `dispute`: 분쟁 증빙과 설문
- `terms_agreement`, `offer`, `settlement`, `notification`: 각 도메인 API
- `admin`: 관리자 액터 전용 API

관리자 API는 현재 계약과 권한 경계를 유지하기 위해 `admin` 패키지에
둔다. 관리자 API가 커져 독립적인 변경 주기를 갖게 되면 별도 설계
결정으로 도메인별 분리를 검토한다.

## 호환성

이 구성은 내부 Python import 경로만 변경한다. 공개 URL, HTTP 메서드,
요청·응답 계약은 유지한다. 이전 평면 모듈 경로를 위한 호환 모듈은
제공하지 않는다.
