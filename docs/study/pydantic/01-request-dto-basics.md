# Pydantic 요청 DTO 기초

> FastAPI에서 HTTP JSON 요청을 검증하고 Python 객체로 변환하는 방법

## 1. Pydantic이란?

Pydantic은 **Python 데이터 검증·변환 라이브러리**다.

FastAPI는 Pydantic 모델을 요청 DTO로 사용한다. 클라이언트가 보낸 JSON이 DTO의 타입과 규칙에 맞는지 검사하고, 성공하면 Python 객체로 변환한다.

이 프로젝트에서는 [`app/schemas/proof.py`](../../../app/schemas/proof.py)의 `ProofDisputeRequest`가 한 예다.

```python
from pydantic import BaseModel, ConfigDict, Field


class ProofDisputeRequest(BaseModel):
    survey_question_id: int = Field(..., validation_alias="surveyQuestionId", ge=1)
    dispute_reason: str = Field(..., validation_alias="disputeReason")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
```

## 2. 요청 DTO가 만들어지는 흐름

```text
HTTP JSON 요청
  → FastAPI
  → ProofDisputeRequest 생성 시도
  → BaseModel/Pydantic이 타입·Field 규칙·모델 설정 검증
  → 성공: DTO 객체 생성
  → 실패: FastAPI가 HTTP 422 응답 생성
```

성공한 뒤 서비스 코드에서는 camelCase 대신 Python 필드명으로 접근한다.

```python
request.survey_question_id
request.dispute_reason
```

## 3. `Field()` — 필드별 규칙 선언

`Field()`는 호출 가능한 함수다. 필드의 검증 규칙과 API 메타데이터를 Pydantic에 선언한다.

```python
survey_question_id: int = Field(..., validation_alias="surveyQuestionId", ge=1)
```

`Field()`가 직접 요청을 검사하는 것이 아니다. `BaseModel`이 입력 데이터로 DTO 객체를 만들 때 `Field()`에 선언한 규칙을 읽어 실제 검증한다.

| 선언 | 의미 |
|---|---|
| `...` | 필수 입력이다. 값이 없으면 검증 오류가 난다. |
| `validation_alias="surveyQuestionId"` | 입력 데이터에서 `surveyQuestionId`라는 이름을 받는다. JSON 요청에서는 camelCase API 필드명을 받는 용도다. |
| `ge=1` | `greater than or equal to 1`의 약자다. 값은 **1 이상**이어야 한다. 1보다 커야 한다면 `gt=1`을 사용한다. |

따라서 다음 요청은 유효하다.

```json
{
  "surveyQuestionId": 3,
  "disputeReason": "수행 내용이 요청과 다릅니다."
}
```

`surveyQuestionId`가 없거나, `0`이면 검증에 실패한다.

## 4. `ConfigDict()` — 모델 전체 설정

`ConfigDict`는 Pydantic 모델의 설정 형식을 나타내는 타입이며, `ConfigDict(...)` 호출은 모델 전체에 적용할 설정을 만든다.

```python
model_config = ConfigDict(extra="forbid", populate_by_name=True)
```

이 설정은 한 필드가 아니라 `ProofDisputeRequest` 전체에 적용된다.

| 설정 | 의미 |
|---|---|
| `extra="forbid"` | DTO에 정의되지 않은 입력 필드를 거부한다. 오타나 API 계약 밖의 데이터를 조용히 무시하지 않는다. |
| `populate_by_name=True` | `validation_alias`뿐 아니라 Python 필드명으로도 입력할 수 있다. |

현재 DTO는 아래 두 요청 형식을 모두 허용한다.

```json
{ "surveyQuestionId": 3, "disputeReason": "사유" }
```

```json
{ "survey_question_id": 3, "dispute_reason": "사유" }
```

반면, 아래 요청은 `unexpectedField`가 정의되어 있지 않아 `extra="forbid"` 설정으로 검증에 실패한다.

```json
{
  "surveyQuestionId": 3,
  "disputeReason": "사유",
  "unexpectedField": "허용되지 않음"
}
```

## 5. `BaseModel`을 상속하는 이유

`BaseModel`은 Pydantic이 제공하는 클래스다. 요청 DTO가 이를 상속하면 다음 기능을 얻는다.

- 타입 검증과 필요한 타입 변환
- `Field()`에 선언한 필수값·범위 등의 규칙 적용
- 중첩 DTO 검증
- 입력 별칭(`validation_alias`)과 출력 별칭 처리
- `model_config` 설정 적용
- `model_dump()`, `model_dump_json()` 같은 직렬화 기능
- FastAPI가 HTTP 422 응답으로 변환할 수 있는 구조화된 검증 오류 생성

```python
class ProofDisputeRequest(BaseModel):
    # Pydantic DTO가 된다.
    pass
```

반대로 `BaseModel`을 상속하지 않은 일반 클래스의 타입 힌트는 기본적으로 런타임 검증을 수행하지 않는다.

```python
class ProofDisputeRequest:
    survey_question_id: int
```

Pydantic 사용 방식이 `BaseModel` 상속만 있는 것은 아니다. `TypeAdapter`나 Pydantic dataclass도 사용할 수 있다. 다만 FastAPI 요청 DTO처럼 필드 규칙, 별칭, OpenAPI 문서 생성, 일관된 오류 응답이 필요한 경우에는 `BaseModel` 상속이 가장 표준적인 방식이다.
