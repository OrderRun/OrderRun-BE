import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.firebase import get_notification_worker, init_fcm
from app.api.v1 import auth, mission, proposal, offer, notifications, admin, settlement, terms, users
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.listeners import notification_listener
from app.schemas.common import ApiResponse
from app.core.openapi import HEALTH_EXAMPLE, ROOT_EXAMPLE, success_response

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    notification_listener.register_all()

    if settings.fcm_credentials_path or settings.fcm_credentials_json:
        init_fcm()
    else:
        logger.warning("FCM credentials not configured — push notifications disabled")

    worker = get_notification_worker()
    _scheduler.add_job(
        worker.retry_failed,
        "interval",
        minutes=5,
        args=[SessionLocal],
        id="retry_failed_notifications",
        replace_existing=True,
    )
    _scheduler.start()

    yield

    _scheduler.shutdown(wait=False)


# Create FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="OrderRun API",
    description="심부름 요청, 제안, 미션, 인증을 제공하는 OrderRun 백엔드 API입니다.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(terms.router)
app.include_router(proposal.router)
app.include_router(offer.router)
app.include_router(mission.router)
app.include_router(settlement.router)
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/", responses={200: success_response(ROOT_EXAMPLE)})
async def root():
    """API 루트 정보를 반환합니다."""
    return {
        "message": "Welcome to OrderRun API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get(
    "/v1/health",
    response_model=ApiResponse[dict[str, str]],
    responses={200: success_response(HEALTH_EXAMPLE)},
)
async def health_check():
    """서버 상태를 확인합니다."""
    return ApiResponse(success=True, data={"status": "UP"}, message="Success")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            operation.get("responses", {}).pop("422", None)
            for response in operation.get("responses", {}).values():
                examples = response.get("content", {}).get("application/json", {}).get("examples", {})
                for example in examples.values():
                    error = example.get("value", {}).get("error")
                    if isinstance(error, dict) and "details" not in error:
                        error["details"] = None

    proposal_detail = openapi_schema["paths"].get("/v1/proposal/{proposal_id}", {}).get("get", {})
    proposal_content = (
        proposal_detail.get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
    )
    proposal_example = proposal_content.get("example") or (
        proposal_content.get("examples", {}).get("without_mission", {}).get("value", {})
    )
    if proposal_example and "example" not in proposal_content:
        proposal_content["example"] = proposal_example
    if isinstance(proposal_example.get("data"), dict):
        proposal_example["data"].setdefault("missionId", None)
    proposal_without_mission = proposal_content.get("examples", {}).get("without_mission", {}).get("value", {})
    if isinstance(proposal_without_mission.get("data"), dict):
        proposal_without_mission["data"].setdefault("missionId", None)

    offer_detail = openapi_schema["paths"].get("/v1/offer/{offer_id}", {}).get("get", {})
    offer_content = (
        offer_detail.get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
    )
    offer_example = offer_content.get("example") or (
        offer_content.get("examples", {}).get("without_mission", {}).get("value", {})
    )
    if offer_example and "example" not in offer_content:
        offer_content["example"] = offer_example
    if isinstance(offer_example.get("data"), dict):
        offer_example["data"].setdefault("missionId", None)
    offer_without_mission = offer_content.get("examples", {}).get("without_mission", {}).get("value", {})
    if isinstance(offer_without_mission.get("data"), dict):
        offer_without_mission["data"].setdefault("missionId", None)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.app_debug,
    )
