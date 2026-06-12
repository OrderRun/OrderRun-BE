# EC2 prod/staging 분리

## 목표

같은 EC2에서 staging 접근은 `http://43.200.56.9`로 유지하고, `api.kkobung-dan.store`는 production, `staging-api.kkobung-dan.store`는 staging으로 분리한다. DNS는 `43.200.56.9`로 연결되었고, SSL은 Let's Encrypt HTTP-01 webroot 방식으로 적용한다.

## 범위

- Redis 없는 EC2 전용 compose 구성 추가
- `app-staging`, `app-prod`, `nginx` 컨테이너 분리
- Nginx HTTP 라우팅 추가
  - `43.200.56.9` 및 기본 요청은 staging
  - `staging-api.kkobung-dan.store` host header는 staging
  - `api.kkobung-dan.store` host header는 prod
- Nginx HTTPS 라우팅 추가
  - `api.kkobung-dan.store`는 HTTPS에서 prod
  - `staging-api.kkobung-dan.store`는 HTTPS에서 staging
  - 도메인 HTTP 요청은 HTTPS로 redirect
  - IP 직접 접근은 staging HTTP 유지
- 배포 스크립트에 `DEPLOY_TARGET=prod|staging` 지원 추가
- EC2 전용 env 예시는 `.env.ec2.example`에 둔다.
- 파일 로그 저장을 위해 앱/Nginx 로그를 `/home/ubuntu/orderrun/logs`에 마운트한다.

## 비범위

- Redis 도입

## 가정

- `43.200.56.9` 직접 접근은 계속 staging으로 사용한다.
- `api.kkobung-dan.store`, `staging-api.kkobung-dan.store`는 `43.200.56.9`로 DNS 연결되어 있다.
- GitHub Secrets 이름은 기존 `STG_*`를 유지하고, workflow에서 compose env인 `STAGING_*`로 매핑한다.
- AWS SNS secrets는 staging/prod가 같은 값을 쓰는 공통 secret으로 유지한다.
- production DB 기본 이름은 `prod_orderun`이다.
- staging DB 이름은 EC2 환경변수 `STAGING_MYSQL_DATABASE`로 주입한다.
- production과 staging은 가능하면 서로 다른 RDS user/password를 사용한다.
- 현재 앱은 Redis에 의존하지 않는다.

## 작업 분해

1. `docker-compose.ec2.yml`에 `app-staging`, `app-prod`, `nginx`를 정의한다.
2. FastAPI 컨테이너는 host port를 열지 않고 Docker network 내부 `8000`만 노출한다.
3. `nginx/templates/ec2-http.conf.template`에서 HTTP 라우팅과 ACME challenge 경로를 정의한다.
4. `nginx/templates/ec2-staging-http.conf.template`에서 prod upstream 없이 staging-only HTTP 라우팅을 정의한다.
5. `nginx/templates/ec2-https.conf.template`에서 HTTPS 라우팅과 HTTP redirect를 정의한다.
6. `nginx`는 app 컨테이너에 `depends_on`하지 않고 독립적으로 실행한다.
7. `scripts/deploy.sh`는 target app만 재배포하고 Nginx를 함께 recreate하지 않는다.
8. staging workflow는 GitHub Secrets로 `.env.ec2`를 생성하고 `DEPLOY_TARGET=staging`으로 배포한다.

## 검증 전략

- compose 설정 검증:
  - `docker compose -f docker-compose.ec2.yml config`
  - `docker compose --env-file .env.ec2.example -f docker-compose.ec2.yml config`
- 스크립트 문법 검증:
  - `bash -n scripts/deploy.sh`
- DNS 검증:
  - `dig +short api.kkobung-dan.store`
  - `dig +short staging-api.kkobung-dan.store`
- EC2 적용 후 staging 확인:
  - `curl http://43.200.56.9/v1/health`
- EC2 적용 후 도메인 확인:
  - `curl http://staging-api.kkobung-dan.store/v1/health`
  - `curl http://api.kkobung-dan.store/v1/health`
- SSL 전환 후 확인:
  - `curl https://staging-api.kkobung-dan.store/v1/health`
  - `curl https://api.kkobung-dan.store/v1/health`
- Redis 제거 확인:
  - `docker ps`에 Redis 컨테이너가 없어야 한다.
- 파일 로그 확인:
  - `tail -f /home/ubuntu/orderrun/logs/staging/app/app.log`
  - `tail -f /home/ubuntu/orderrun/logs/prod/app/app.log`
  - `tail -f /home/ubuntu/orderrun/logs/nginx/staging-access.log`
  - `tail -f /home/ubuntu/orderrun/logs/nginx/prod-access.log`

## 롤아웃 메모

1. RDS에 `prod_orderun` DB와 production DB user를 먼저 준비한다.
2. staging workflow가 EC2에 `.env.ec2`를 생성한다.
3. 첫 배포 전 로그 디렉토리와 Nginx 로그 순환 설정을 준비한다.
   - `mkdir -p /home/ubuntu/orderrun/logs/{staging/app,prod/app,nginx}`
   - `sudo ./scripts/install-logrotate.sh`
   - `sudo logrotate -d /etc/logrotate.d/orderrun`
4. staging workflow는 기존 staging compose 컨테이너가 남아 있으면 첫 전환 시에만 `orderrun-app-staging`, `orderrun-nginx-staging`, `orderrun-redis-staging`를 정리한다.
5. `COMPOSE_FILE=docker-compose.ec2.yml COMPOSE_ENV_FILE=.env.ec2 DEPLOY_TARGET=staging ./deploy.sh`로 staging app만 배포한다.
6. `docker compose --env-file .env.ec2 -f docker-compose.ec2.yml up -d --build nginx`로 staging-only Nginx 템플릿을 적용한다.
7. `COMPOSE_FILE=docker-compose.ec2.yml COMPOSE_ENV_FILE=/home/ubuntu/orderrun/.env.ec2 DEPLOY_TARGET=prod ./scripts/deploy.sh`는 production DB/env 준비 후 별도로 실행한다.
8. HTTP 도메인 접근이 정상인지 확인한다.
9. 인증서를 발급한다.
   - `docker compose --env-file /home/ubuntu/orderrun/.env.ec2 -f docker-compose.ec2.yml --profile ssl run --rm certbot`
10. EC2 `.env.ec2`의 `NGINX_TEMPLATE`를 `./nginx/templates/ec2-https.conf.template`로 변경한다.
11. `docker compose --env-file /home/ubuntu/orderrun/.env.ec2 -f docker-compose.ec2.yml up -d --build nginx`로 Nginx를 재생성한다.

## 남은 리스크

- `docker compose pull`은 `DOCKER_IMAGE`가 registry 이미지일 때 안정적이다. 로컬 빌드만 사용할 경우 이미지 pull 정책을 조정해야 한다.
- HTTPS 템플릿은 `api.kkobung-dan.store`를 인증서 이름으로 사용한다. certbot 발급 시 `api.kkobung-dan.store`를 첫 번째 `-d` 값으로 유지해야 한다.
- Nginx는 app 컨테이너와 독립 실행되므로, 아직 뜨지 않은 upstream 라우트만 실패하고 다른 라우트는 계속 동작한다.
