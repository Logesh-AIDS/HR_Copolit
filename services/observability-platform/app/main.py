from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.delivery.http import tracing_router, metrics_router, alerting_router, incident_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "observability-platform"}

app.include_router(tracing_router.router, prefix=settings.API_V1_STR)
app.include_router(metrics_router.router, prefix=settings.API_V1_STR)
app.include_router(alerting_router.router, prefix=settings.API_V1_STR)
app.include_router(incident_router.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8006, reload=True)
