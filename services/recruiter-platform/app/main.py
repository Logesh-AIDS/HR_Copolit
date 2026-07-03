from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.delivery.http import candidate_router, comparison_router, search_router, report_router

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
    return {"status": "ok", "service": "recruiter-platform"}

app.include_router(candidate_router.router, prefix=settings.API_V1_STR)
app.include_router(comparison_router.router, prefix=settings.API_V1_STR)
app.include_router(search_router.router, prefix=settings.API_V1_STR)
app.include_router(report_router.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8007, reload=True)
