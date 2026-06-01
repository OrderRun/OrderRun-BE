from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.api.v1 import auth, mission, proposal, offer, notifications, admin, settlement, terms, users
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.schemas.common import ApiResponse

# Create FastAPI app
app = FastAPI(
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


@app.get("/")
async def root():
    """API 루트 정보를 반환합니다."""
    return {
        "message": "Welcome to OrderRun API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/v1/health", response_model=ApiResponse[dict[str, str]])
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
            for response in operation.get("responses", {}).values():
                examples = response.get("content", {}).get("application/json", {}).get("examples", {})
                for example in examples.values():
                    error = example.get("value", {}).get("error")
                    if isinstance(error, dict) and "details" not in error:
                        error["details"] = None

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
