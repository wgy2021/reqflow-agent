from fastapi import FastAPI

from app.routers.requirements import router as requirements_router
from app.routers.system import router as system_router
from app.routers.knowledge import router as knowledge_router

app = FastAPI(
    title="ReqFlow Agent API",
    version="0.1.0",
)


app.include_router(requirements_router)
app.include_router(system_router)
app.include_router(knowledge_router)


@app.get(
    "/health",
    tags=["system.py"],
)
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "reqflow-agent",
        "environment": "development",
    }