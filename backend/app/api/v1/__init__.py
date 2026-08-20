from app.api.v1 import auth, documents, analysis, interviews

api_router = auth.router
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])