# OrderRun 로컬 개발 환경 세팅

## 1. 목적

이 문서는 `OrderRun-BE` 학습 프로젝트를 로컬에서 시작할 때 필요한 Python 가상환경 설정과 기본 패키지 설치 절차를 단계별로 정리한다.

구현 코드를 실행하거나 수정하기 전에 먼저 이 절차로 개발 환경을 맞춘다.

## 2. 전제 조건

- macOS 또는 Linux 셸 환경
- `python3.12` 설치 완료
- 프로젝트 루트 경로 확인 완료

프로젝트 루트:

```bash
/Users/dustin.hwang/Documents/GitHub/OrderRun-BE
```

## 3. 1단계: 프로젝트 폴더로 이동

터미널에서 프로젝트 루트로 이동한다.

```bash
cd /Users/dustin.hwang/Documents/GitHub/OrderRun-BE
```

현재 위치 확인:

```bash
pwd
```

예상 결과:

```bash
/Users/dustin.hwang/Documents/GitHub/OrderRun-BE
```

## 4. 2단계: Python 설치 확인

가상환경 생성 전에 `python3`가 동작하는지 확인한다.

```bash
python3.12 --version
```

예상 결과 예시:

```bash
Python 3.12.x
```

## 5. 3단계: 가상환경 생성

프로젝트 전용 Python 가상환경을 만든다.

```bash
python3.12 -m venv .venv
```

설명:

- `.venv`는 프로젝트 전용 Python 실행 파일과 패키지 저장 공간이다.
- 전역 Python 환경과 분리되므로 학습 중 패키지 충돌을 줄일 수 있다.

이미 `.venv/` 폴더가 있으면 이 단계는 건너뛴다.

## 6. 4단계: 가상환경 활성화

생성한 가상환경을 현재 터미널 세션에 활성화한다.

```bash
source .venv/bin/activate
```

활성화가 정상이라면 셸 앞에 `(.venv)`가 표시된다.

예시:

```bash
(.venv) dustin.hwang@macbook OrderRun-BE %
```

## 7. 5단계: pip 업그레이드

패키지 설치 도구를 최신 상태로 맞춘다.

```bash
pip install --upgrade pip
```

## 8. 6단계: 의존성 설치

프로젝트에 필요한 Python 패키지를 설치한다.

```bash
pip install -e ".[dev]"
```

설명:

- 이 명령은 반드시 가상환경 활성화 이후에 실행한다.
- 설치 대상은 `pyproject.toml`의 기본 의존성과 `dev` extra다.
- 설치 대상은 전역 환경이 아니라 `.venv` 내부다.

## 9. 7단계: 가상환경 적용 확인

현재 사용 중인 Python과 pip가 가상환경 경로를 가리키는지 확인한다.

```bash
which python
which pip
python --version
```

정상 예시:

```bash
/Users/dustin.hwang/Documents/GitHub/OrderRun-BE/.venv/bin/python
/Users/dustin.hwang/Documents/GitHub/OrderRun-BE/.venv/bin/pip
Python 3.12.x
```

## 10. 8단계: 다음 작업을 위한 재진입 방법

터미널을 새로 열면 가상환경은 자동으로 유지되지 않는다.

작업을 다시 시작할 때마다 아래 순서로 진입한다.

```bash
cd /Users/dustin.hwang/Documents/GitHub/OrderRun-BE
source .venv/bin/activate
```

## 11. 9단계: 작업 종료 후 비활성화

가상환경 사용을 마치면 아래 명령으로 빠져나온다.

```bash
deactivate
```

## 12. 자주 헷갈리는 점

- `source .venv/bin/activate`는 `.venv` 폴더가 이미 있을 때 사용하는 명령이다.
- `.venv` 폴더가 없으면 먼저 `python3.12 -m venv .venv`를 실행해야 한다.
- 새 터미널 세션에서는 다시 활성화해야 한다.
- `.venv/` 폴더는 보통 Git에 커밋하지 않는다.
- macOS/Linux 기준 명령은 `source .venv/bin/activate`다.

## 13. 최소 시작 명령 요약

처음 1회:

```bash
cd /Users/dustin.hwang/Documents/GitHub/OrderRun-BE
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

그다음부터:

```bash
cd /Users/dustin.hwang/Documents/GitHub/OrderRun-BE
source .venv/bin/activate
```
